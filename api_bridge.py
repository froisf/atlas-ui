import os
import re
import time
import requests
import subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
COBOL_ROOT = Path(
    os.getenv("COBOL_ROOT", r"D:\Workspace\01-Products\nw-poc\legacy-cobol")
).resolve()
BASE_SANDBOX = Path(os.getcwd()) / "_limpo"
TIMEOUT_SEC = 300
MAX_TENTATIVAS = 3

BASE_SANDBOX.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Atlas Agentic API Enterprise")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


class ConvertRequest(BaseModel):
    arquivo: str
    cliente: str = "mock-xpto"


class ChatRequest(BaseModel):
    message: str


POM_XML_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.3</version>
        <relativePath/>
    </parent>
    <groupId>com.ifroix</groupId>
    <artifactId>atlas-program</artifactId>
    <version>1.0.0</version>
    <properties><java.version>21</java.version></properties>
    <dependencies>
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter</artifactId></dependency>
    </dependencies>
</project>
"""


def safe_read_cobol(filename: str) -> str:
    target_path = (COBOL_ROOT / filename).resolve()
    if not str(target_path).startswith(str(COBOL_ROOT)):
        raise HTTPException(status_code=403, detail="Acesso negado: Path traversal.")
    if not target_path.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(
                "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO-WORLD.\n       PROCEDURE DIVISION.\n           DISPLAY 'HELLO, ATLAS AGENTIC!'.\n           STOP RUN.\n"
            )
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


def build_prompt(cobol_code: str, class_name: str) -> str:
    return f"""Você é um engenheiro de software sênior especialista em modernização de sistemas legados.
Sua tarefa é converter o código COBOL fornecido abaixo para Java 21 com Spring Boot 3.
REGRAS OBRIGATÓRIAS:
1. O nome da classe pública DEVE SER EXATAMENTE: {class_name}
2. O pacote DEVE SER: package com.ifroix.atlas;
3. Preserve a lógica original EXATAMENTE como está.
4. Use recursos modernos do Java 21.
5. A classe DEVE ter a anotação @Service (do Spring).
6. É ESTRITAMENTE PROIBIDO criar o método `public static void main(String[] args)`. 
7. A lógica do COBOL (DISPLAY, cálculos) deve ficar dentro de um método público normal (ex: `public void executarLogica()`).
8. Retorne APENAS o código Java.

Código COBOL:
{cobol_code}
"""


def build_ir_prompt(cobol_code: str, class_name: str) -> str:
    return f"""Você é um engenheiro de software sênior especialista em análise de sistemas legados.
Sua tarefa é ler o código COBOL abaixo e extrair a LÓGICA DE NEGÓCIO em formato JSON (IR Canônica).
REGRAS:
1. O JSON deve conter: "program_id", "variaveis" (nome e tipo), e "fluxo" (lista de ações como DISPLAY, MOVE, IF, PERFORM, CALL).
2. Não gere código Java. Apenas o JSON.
3. Retorne APENAS o JSON, sem formatação markdown.
Código COBOL:
{cobol_code}
"""


def build_java_from_ir_prompt(ir_json: str, class_name: str) -> str:
    return f"""Você é um engenheiro de software sênior especialista em modernização.
Sua tarefa é escrever código Java 21 com Spring Boot 3 baseado na representação JSON (IR) abaixo.

REGRAS OBRIGATÓRIAS:
1. O nome da classe DEVE SER: {class_name}
2. O pacote DEVE SER: package com.ifroix.atlas;
3. A classe DEVE ter a anotação @Service.
4. A lógica DEVE estar dentro do método `public void executarLogica()`.
5. É ESTRITAMENTE PROIBIDO criar o método `public static void main`.
6. NÃO crie arrays genéricos ou instâncias de `Object` para representar o JSON. Use a IR apenas como um GUIA para escrever código Java idiomático.
   Exemplo: Se a IR tem o fluxo ["DISPLAY", "HELLO"], escreva `System.out.println("HELLO");`.
7. Declare as variáveis com os tipos Java corretos (int, String, double, etc.) baseados na lógica da IR.
8. Retorne APENAS o código Java.

IR JSON:
{ir_json}
"""


def build_correction_prompt(
    previous_code: str, compile_error: str, class_name: str
) -> str:
    return f"""O código Java Spring Boot que você gerou tem erros de compilação.
Código com erro:
{previous_code}
Erro do Maven:
{compile_error}
CORRIJA o código Java. Mantenha o pacote com.ifroix.atlas e a classe {class_name}.
Retorne APENAS o código Java corrigido.
"""


def extract_java(llm_output: str, expected_class_name: str) -> tuple[str, list[str]]:
    warnings = []
    match = re.search(
        r"```(?:java|markdown)?\s*(.*?)```", llm_output, re.DOTALL | re.IGNORECASE
    )
    raw_code = match.group(1).strip() if match else llm_output.strip()
    start_match = re.search(r"(package\s+|import\s+|public\s+class\s+)", raw_code)
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
    if f"class {expected_class_name}" not in java_code:
        warnings.append(f"Atenção: A classe não se chama {expected_class_name}.")
    return java_code, warnings


def remove_main_method(java_code: str) -> str:
    padrao = r"public\s+static\s+void\s+main\s*\([^)]*\)\s*\{[^}]*\}"
    return re.sub(padrao, "", java_code, flags=re.DOTALL)


@app.post("/api/convert")
async def convert_cobol(req: ConvertRequest):
    start_time = time.time()
    class_name = Path(req.arquivo).stem.capitalize()
    cobol_code = safe_read_cobol(req.arquivo)
    program_dir = BASE_SANDBOX / req.cliente / Path(req.arquivo).stem
    java_pkg_dir = program_dir / "src" / "main" / "java" / "com" / "ifroix" / "atlas"
    java_pkg_dir.mkdir(parents=True, exist_ok=True)
    with open(program_dir / "pom.xml", "w", encoding="utf-8") as f:
        f.write(POM_XML_TEMPLATE)
    out_filename = f"{class_name}.java"
    out_path = java_pkg_dir / out_filename
    tentativa = 1
    compile_error = None
    java_code = ""
    warnings = []

    while tentativa <= MAX_TENTATIVAS:
        print(f"🔄 Tentativa {tentativa} para {class_name}...")
        prompt = (
            build_prompt(cobol_code, class_name)
            if tentativa == 1
            else build_correction_prompt(java_code, compile_error, class_name)
        )
        llm_raw = call_ollama(prompt, temperature=0.1)
        java_code, warnings = extract_java(llm_raw, class_name)
        java_code = remove_main_method(java_code)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(java_code)
        compile_error = None
        try:
            try:
                result = subprocess.run(
                    ["mvn", "clean", "compile"],
                    cwd=program_dir,
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT_SEC,
                )
            except FileNotFoundError:
                mvn_path = r"C:\apache-maven-3.9.16\bin\mvn.cmd"
                result = subprocess.run(
                    [mvn_path, "clean", "compile"],
                    cwd=program_dir,
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT_SEC,
                )
            if result.returncode == 0:
                print(f"✅ Maven compilou com sucesso na tentativa {tentativa}!")
                break
            else:
                compile_error = result.stdout
                print(f"❌ Erro de compilação Maven na tentativa {tentativa}.")
        except FileNotFoundError:
            warnings.append("ERRO CRÍTICO: 'mvn' não encontrado.")
            break
        except subprocess.TimeoutExpired:
            compile_error = "Timeout: O Maven demorou mais de 5 minutos."
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


@app.post("/api/convert_ir")
async def convert_cobol_ir(req: ConvertRequest):
    start_time = time.time()
    class_name = Path(req.arquivo).stem.capitalize()
    cobol_code = safe_read_cobol(req.arquivo)
    program_dir = BASE_SANDBOX / req.cliente / Path(req.arquivo).stem
    java_pkg_dir = program_dir / "src" / "main" / "java" / "com" / "ifroix" / "atlas"
    java_pkg_dir.mkdir(parents=True, exist_ok=True)
    with open(program_dir / "pom.xml", "w", encoding="utf-8") as f:
        f.write(POM_XML_TEMPLATE)
    out_filename = f"{class_name}.java"
    out_path = java_pkg_dir / out_filename

    print(f"🔄 [IR] Etapa 1: Extraindo JSON do COBOL {req.arquivo}...")
    ir_prompt = build_ir_prompt(cobol_code, class_name)
    ir_raw = call_ollama(ir_prompt, temperature=0.1)
    ir_json = re.sub(
        r"```(?:json)?\s*(.*?)```", r"\1", ir_raw, flags=re.DOTALL | re.IGNORECASE
    ).strip()

    print(f"🔄 [IR] Etapa 2: Gerando Java Spring Boot a partir da IR...")
    java_prompt = build_java_from_ir_prompt(ir_json, class_name)
    java_code, warnings = extract_java(
        call_ollama(java_prompt, temperature=0.1), class_name
    )
    java_code = remove_main_method(java_code)

    tentativa = 1
    compile_error = None
    while tentativa <= MAX_TENTATIVAS:
        print(f"🔄 [IR] Tentativa Maven {tentativa} para {class_name}...")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(java_code)
        compile_error = None
        try:
            try:
                result = subprocess.run(
                    ["mvn", "clean", "compile"],
                    cwd=program_dir,
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT_SEC,
                )
            except FileNotFoundError:
                mvn_path = r"C:\apache-maven-3.9.16\bin\mvn.cmd"
                result = subprocess.run(
                    [mvn_path, "clean", "compile"],
                    cwd=program_dir,
                    capture_output=True,
                    text=True,
                    timeout=TIMEOUT_SEC,
                )
            if result.returncode == 0:
                print(f"✅ [IR] Maven compilou com sucesso na tentativa {tentativa}!")
                break
            else:
                compile_error = result.stdout
                print(
                    f"❌ [IR] Erro Maven na tentativa {tentativa}. Solicitando correção..."
                )
                correction_prompt = build_correction_prompt(
                    java_code, compile_error, class_name
                )
                java_code, warnings = extract_java(
                    call_ollama(correction_prompt, temperature=0.1), class_name
                )
                java_code = remove_main_method(java_code)
        except Exception as e:
            warnings.append(f"Erro crítico: {str(e)}")
            break
        tentativa += 1

    duration = int((time.time() - start_time) * 1000)
    return {
        "ok": compile_error is None and len(warnings) == 0,
        "java_path": str(out_path.absolute()),
        "java_code": java_code,
        "ir_json": ir_json,
        "warnings": warnings,
        "compile_error": compile_error,
        "tentativas": tentativa,
        "duration_ms": duration,
        "model": MODEL,
    }


@app.post("/api/chat")
async def chat_with_ollama(req: ChatRequest):
    prompt = f"Você é o Atlas, assistente sênior. Responda curto: {req.message}"
    return {"response": call_ollama(prompt, temperature=0.3).strip()}


if __name__ == "__main__":
    import uvicorn

    print("🚀 Atlas API v4.1 (IR Canônica Refinada) rodando na porta 8000!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
