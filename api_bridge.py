import os
import re
import time
import requests
import subprocess
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
MAX_TENTATIVAS = 3

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


class ChatRequest(BaseModel):
    message: str


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


def call_ollama(prompt: str, temperature: float = 0.1) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SEC)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=502, detail="Ollama não está rodando.")
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504, detail=f"Timeout: Ollama demorou mais de {TIMEOUT_SEC}s."
        )


def build_prompt(cobol_code: str, class_name: str) -> str:
    return f"""Você é um engenheiro de software sênior especialista em modernização de sistemas legados.
Sua tarefa é converter o código COBOL fornecido abaixo para Java 21 puro.

REGRAS OBRIGATÓRIAS:
1. O nome da classe pública DEVE SER EXATAMENTE: {class_name}
2. Preserve a lógica original EXATAMENTE como está.
3. Use recursos modernos do Java 21 (ex: `var`, API `java.nio.file.Files` e `Path`).
4. Use `try-with-resources`.
5. Não invente bibliotecas externas.
6. Retorne APENAS o código Java.

Código COBOL:
{cobol_code}
"""


def build_correction_prompt(
    previous_code: str, compile_error: str, class_name: str
) -> str:
    return f"""O código Java que você gerou anteriormente tem erros de compilação e não pode ser usado.
Aqui está o código Java com erro:
{previous_code}

Aqui está a mensagem de erro exata do compilador javac:
{compile_error}

Sua tarefa é CORRIGIR o código Java acima para que ele compile perfeitamente.
Mantenha as regras originais:
1. O nome da classe pública DEVE SER EXATAMENTE: {class_name}
2. Use Java 21 puro.
3. Retorne APENAS o código Java corrigido.
"""


def extract_java(llm_output: str, expected_class_name: str) -> tuple[str, list[str]]:
    warnings = []
    match = re.search(
        r"```(?:java|markdown)?\s*(.*?)```", llm_output, re.DOTALL | re.IGNORECASE
    )

    if match:
        raw_code = match.group(1).strip()
    else:
        raw_code = llm_output.strip()

    start_match = re.search(
        r"(import\s+|package\s+|public\s+class\s+|public\s+record\s+|class\s+)",
        raw_code,
    )
    if start_match:
        java_code = raw_code[start_match.start() :]
    else:
        inicio = raw_code.find("{")
        java_code = raw_code[inicio:] if inicio != -1 else raw_code

    fim = java_code.rfind("}")
    if fim != -1:
        java_code = java_code[: fim + 1]

    if java_code.count("{") != java_code.count("}"):
        warnings.append("Atenção: Chaves desbalanceadas.")
    if (
        f"class {expected_class_name}" not in java_code
        and f"record {expected_class_name}" not in java_code
    ):
        warnings.append(f"Atenção: A classe não se chama {expected_class_name}.")

    return java_code, warnings


# ==========================================
# 4. ENDPOINT PRINCIPAL (COM AUTO-CORREÇÃO)
# ==========================================
@app.post("/api/convert")
async def convert_cobol(req: ConvertRequest):
    start_time = time.time()
    class_name = Path(req.arquivo).stem.capitalize()
    cobol_code = safe_read_cobol(req.arquivo)

    out_filename = f"{class_name}.java"
    out_path = JAVA_ROOT / out_filename

    tentativa = 1
    compile_error = None
    java_code = ""
    warnings = []

    # Loop de tentativas
    while tentativa <= MAX_TENTATIVAS:
        print(f"🔄 Tentativa {tentativa} de conversão para {class_name}...")

        if tentativa == 1:
            prompt = build_prompt(cobol_code, class_name)
        else:
            # Se não for a primeira, usa o prompt de correção com o erro do javac
            prompt = build_correction_prompt(java_code, compile_error, class_name)

        llm_raw = call_ollama(prompt, temperature=0.1)
        java_code, warnings = extract_java(llm_raw, class_name)

        # Salva o arquivo para testar
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(java_code)

        # Testa com o javac
        compile_error = None
        try:
            result = subprocess.run(
                ["javac", out_filename],
                cwd=JAVA_ROOT,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                print(f"✅ Compilação bem-sucedida na tentativa {tentativa}!")
                break  # Sai do loop se compilar
            else:
                compile_error = result.stderr
                print(
                    f"❌ Erro de compilação na tentativa {tentativa}. Solicitando correção à IA..."
                )
        except FileNotFoundError:
            warnings.append("Aviso: 'javac' não encontrado no PATH.")
            break
        except subprocess.TimeoutExpired:
            compile_error = "Timeout: O compilador demorou muito."
            break

        tentativa += 1

    duration = int((time.time() - start_time) * 1000)

    return {
        "ok": compile_error is None and len(warnings) == 0,
        "java_path": str(out_path.absolute()),
        "java_code": java_code,
        "warnings": warnings,
        "compile_error": compile_error,
        "tentativas": tentativa,
        "duration_ms": duration,
        "model": MODEL,
    }


# ==========================================
# 5. ENDPOINT DE CHAT
# ==========================================
@app.post("/api/chat")
async def chat_with_ollama(req: ChatRequest):
    prompt = f"""Você é o Atlas, um assistente corporativo sênior especialista em modernização de sistemas.
Responda à mensagem do usuário de forma clara e curta.

Mensagem: {req.message}
"""
    llm_raw = call_ollama(prompt, temperature=0.3)
    return {"response": llm_raw.strip()}


if __name__ == "__main__":
    import uvicorn

    print("🚀 Atlas API v2.1 (Com Auto-Correção) rodando na porta 8000!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
