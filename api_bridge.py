import os
import re
import time
import requests
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

COBOL_ROOT = Path(
    os.getenv("COBOL_ROOT", r"D:\Workspace\01-Products\nw-poc\legacy-cobol")
).resolve()
JAVA_ROOT = (
    Path(os.getcwd())
    / "src"
    / "main"
    / "java"
    / "com"
    / "ifroix"
    / "orders"
    / "programs"
)
TIMEOUT_SEC = 180

JAVA_ROOT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Atlas Agentic API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 2. MODELOS DE DADOS
# ==========================================
class ConvertRequest(BaseModel):
    arquivo: str


class ConvertResponse(BaseModel):
    ok: bool
    java_path: str
    java_code: str
    warnings: list[str]
    duration_ms: int
    model: str


# ==========================================
# 3. SERVIÇOS
# ==========================================
def safe_read_cobol(filename: str) -> str:
    target_path = (COBOL_ROOT / filename).resolve()
    if not str(target_path).startswith(str(COBOL_ROOT)):
        raise HTTPException(status_code=403, detail="Acesso negado: Path traversal.")

    if not target_path.exists():
        print(f"⚠️ Arquivo {filename} não encontrado. Gerando um COBOL de teste...")
        mock_cobol = """       IDENTIFICATION DIVISION.
       PROGRAM-ID. HELLO-WORLD.
       PROCEDURE DIVISION.
           DISPLAY 'HELLO, ATLAS AGENTIC!'.
           STOP RUN.
"""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(mock_cobol)

    with open(target_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def build_prompt(cobol_code: str, class_name: str) -> str:
    return f"""Você é um engenheiro de software sênior especialista em modernização de sistemas legados.
Sua tarefa é converter o código COBOL fornecido abaixo para Java 21 puro (sem frameworks como Spring).

REGRAS OBRIGATÓRIAS:
1. O nome da classe pública DEVE SER EXATAMENTE: {class_name}
2. Preserve a lógica original EXATAMENTE como está.
3. Use recursos modernos do Java 21 (ex: `var`, API `java.nio.file.Files` e `Path`).
4. Use `try-with-resources` para fechar arquivos automaticamente.
5. Não invente bibliotecas externas.
6. Retorne APENAS o código Java, envolvido em um bloco de markdown.

Código COBOL:
{cobol_code}
"""


def extract_java(llm_output: str, expected_class_name: str) -> tuple[str, list[str]]:
    warnings = []

    # Tenta achar o bloco markdown
    match = re.search(
        r"```(?:java|markdown)?\s*(.*?)```", llm_output, re.DOTALL | re.IGNORECASE
    )

    if match:
        raw_code = match.group(1).strip()
    else:
        warnings.append("Llama não retornou bloco markdown. Extraindo código bruto.")
        raw_code = llm_output.strip()

    # LIMPEZA 1: Acha o início real do código Java
    start_match = re.search(
        r"(import\s+|package\s+|public\s+class\s+|public\s+record\s+|class\s+)",
        raw_code,
    )
    if start_match:
        java_code = raw_code[start_match.start() :]
    else:
        inicio = raw_code.find("{")
        java_code = raw_code[inicio:] if inicio != -1 else raw_code

    # LIMPEZA 2: Acha o final real do código Java (última chave)
    fim = java_code.rfind("}")
    if fim != -1:
        java_code = java_code[: fim + 1]
    else:
        warnings.append(
            "Não foi possível encontrar o final da classe (chave '}' ausente)."
        )

    # Validações
    if java_code.count("{") != java_code.count("}"):
        warnings.append("Atenção: Chaves desbalanceadas no código Java gerado.")

    if (
        f"class {expected_class_name}" not in java_code
        and f"record {expected_class_name}" not in java_code
    ):
        warnings.append(f"Atenção: A classe gerada não se chama {expected_class_name}.")

    return java_code, warnings


# ==========================================
# 4. ENDPOINT PRINCIPAL
# ==========================================
@app.post("/api/convert")
async def convert_cobol(req: ConvertRequest):
    start_time = time.time()

    class_name = Path(req.arquivo).stem.capitalize()
    cobol_code = safe_read_cobol(req.arquivo)

    prompt = build_prompt(cobol_code, class_name)
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SEC)
        response.raise_for_status()
        llm_raw = response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Ollama não está rodando.")
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504, detail=f"Timeout: Ollama demorou mais de {TIMEOUT_SEC}s."
        )

    java_code, warnings = extract_java(llm_raw, class_name)

    out_filename = f"{class_name}.java"
    out_path = JAVA_ROOT / out_filename

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(java_code)

    duration = int((time.time() - start_time) * 1000)

    return {
        "ok": len(warnings) == 0,
        "java_path": str(out_path.absolute()),
        "java_code": java_code,
        "warnings": warnings,
        "duration_ms": duration,
        "model": MODEL,
    }


# ==========================================
# 5. ENDPOINT DE CHAT (NOVO)
# ==========================================
class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat_with_ollama(req: ChatRequest):
    prompt = f"""Você é o Atlas, um assistente corporativo sênior especialista em modernização de sistemas (COBOL para Java).
Você é direto, educado e focado em resolver problemas técnicos.
Responda à mensagem do usuário abaixo de forma clara e curta.

Mensagem do usuário: {req.message}
"""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3},
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SEC)
        response.raise_for_status()
        llm_raw = response.json().get("response", "")

        return {"response": llm_raw.strip()}
    except Exception as e:
        return {
            "response": f"Desculpe, meu cérebro (Ollama) está offline. Erro: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Atlas API v2.0 (FastAPI) rodando na porta 8000!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
# FIM DO ARQUIVO - COPIE ATÉ AQUI
