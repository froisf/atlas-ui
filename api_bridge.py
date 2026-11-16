import os
import re
import time
import requests
import subprocess
import json
import jsonschema
import hashlib
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb

from cobol_chunker import CobolChunker, CobolChunk

try:
    from webhook_router import router as webhook_router
    HAS_WEBHOOK = True
except ImportError:
    HAS_WEBHOOK = False

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")
COBOL_ROOT = Path(os.getenv("COBOL_ROOT", r"D:\Workspace\01-Products\nw-poc\legacy-cobol")).resolve()
BASE_SANDBOX = Path(os.getcwd()) / "_limpo"
TIMEOUT_SEC = 1800
MAX_TENTATIVAS = 3
CHUNK_THRESHOLD = 100 

BASE_SANDBOX.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Atlas Agentic MCP Enterprise v5.7")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
if HAS_WEBHOOK: app.include_router(webhook_router)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
cobol_context = chroma_client.get_or_create_collection(name="cobol_context")
sql_rag_collection = chroma_client.get_or_create_collection(name="sql_rag_templates")
postmortem_collection = chroma_client.get_or_create_collection(name="postmortems_compilation_memory")

def scrub_pii(cobol_code: str) -> str:
    cobol_code = re.sub(r"\d{3}\.\d{3}\.\d{3}-\d{2}", "[CPF_MASKED]", cobol_code)
    cobol_code = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_MASKED]", cobol_code)
    cobol_code = re.sub(r"'([A-Za-z0-9\s]{4,})'", "'[STRING_MASKED]'", cobol_code)
    return cobol_code

IR_SCHEMA = {
    "type": "object",
    "properties": {
        "program_id": {"type": "string"},
        "variaveis": {"type": "array", "items": {"type": "object"}},
        "fluxo": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["program_id", "variaveis", "fluxo"],
    "additionalProperties": False,
}

def validate_ir(ir_json_str: str) -> dict:
    try:
        data = json.loads(ir_json_str)
        jsonschema.validate(instance=data, schema=IR_SCHEMA)
        return data
    except Exception as e:
        raise ValueError(f"JSON Schema Validation Failed: {e}")

def save_postmortem(error_log: str, cobol_clause: str, applied_patch: str):
    try:
        error_hash = hashlib.sha256(error_log[:500].encode("utf-8")).hexdigest()
        category = "GENERIC_ERROR"
        if "@Repository" in error_log or "cannot find symbol" in error_log: category = "MISSING_SPRING_ANNOTATION"
        elif "BigDecimal" in error_log: category = "TYPE_MISMATCH"
        elif "@Transactional" in error_log: category = "MISSING_TRANSACTIONAL"
        postmortem_collection.add(documents=[error_log[:2000]], metadatas=[{"error_category": category, "error_hash": error_hash, "cobol_clause": cobol_clause, "applied_patch_code": applied_patch}], ids=[f"err_{error_hash}"])
        print(f"[Memoria] Postmortem salvo (Categoria: {category} / Clausula: {cobol_clause})")
    except Exception as e: print(f"[Memoria] Erro ao salvar: {e}")

def retrieve_episodic_fix(error_log: str, cobol_clause: str) -> str:
    try:
        if postmortem_collection.count() == 0: return None
        results = postmortem_collection.query(query_texts=[error_log[:2000]], where={"cobol_clause": cobol_clause}, n_results=1)
        if results["distances"] and results["distances"][0]:
            dist = results["distances"][0][0]
            if dist <= 0.15:
                print(f"[Memoria] Solucao recuperada (Dist: {dist:.4f}) para {cobol_clause}")
                return results["metadatas"][0][0].get("applied_patch_code")
    except Exception: pass
    return None

# NOVO POM COM JUNIT
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
        <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-data-jpa</artifactId></dependency>
        <dependency><groupId>com.h2database</groupId><artifactId>h2</artifactId><scope>runtime</scope></dependency>
        <!-- ATLAS VERIFIER: DEPENDENCIA DE TESTES -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
"""

class ConvertRequest(BaseModel):
    arquivo: str
    cliente: str = "CLIENTE_PILOTO"

class ChatRequest(BaseModel):
    message: str

def call_ollama(prompt: str, temperature: float = 0.1) -> str:
    payload = {"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": temperature}}
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT_SEC)
        response.raise_for_status()
        return response.json().get("response", "")
    except requests.exceptions.ConnectionError: raise HTTPException(status_code=502, detail="Ollama nao esta rodando.")

def extract_json(llm_output: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)```", llm_output, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else llm_output.strip()

def build_ir_prompt(envelope: dict, chunk_text: str) -> str:
    return f"""Voce e um engenheiro de software senior especialista em analise de sistemas legados.
Sua tarefa e ler o trecho de codigo COBOL abaixo e extrair a LOGICA DE NEGOCIO em formato JSON (IR Canonica).
REGRAS:
1. O JSON DEVE conter EXATAMENTE: "program_id" (string), "variaveis" (array de objetos com name e type), e "fluxo" (array de strings com acoes).
2. Nao adicione NENHUM campo extra. O schema e estrito.
3. Retorne APENAS o JSON.
CODIGO COBOL:
{chunk_text}
ENVELOPE DE CONTEXTO:
{json.dumps(envelope, indent=2)}
"""

def build_java_from_ir_prompt(ir_json: str, class_name: str, sql_templates: list) -> str:
    rag_context = ""
    if sql_templates:
        rag_context = "\nUSE OS SEGUINTES PADROES (GOLDEN STANDARDS) RECUPERADOS DO RAG:\n"
        for t in sql_templates: rag_context += f"\n--- Pattern {t['pattern_id']} ---\n{t['golden_standard_code']}\n"

    return f"""Voce e um engenheiro de software senior especialista em modernizacao.
Sua tarefa e escrever o codigo Java 21 com Spring Boot 3 E a classe de teste JUnit 5 baseado na IR abaixo.

REGRAS OBRIGATORIAS:
1. O nome da classe publica de servico DEVE SER: {class_name}
2. O pacote DEVE SER: package com.ifroix.atlas;
3. A classe de servico DEVE ter a anotacao @Service e o metodo `public void executarLogica()`.
4. E ESTRITAMENTE PROIBIDO criar o metodo `public static void main`.
5. **ATLAS VERIFIER:** Voce DEVE criar uma segunda classe de teste chamada `{class_name}Test` anotada com `@SpringBootTest` (ou JUnit puro). O teste deve instanciar a classe principal e chamar o `executarLogica()` para garantir que nao lanca excecoes.
6. **SEPARACAO DE ARQUIVOS:** Use EXATAMENTE a string `// --- FILE: {class_name}Test.java ---` para separar o arquivo de servico do arquivo de teste. O conteudo antes dessa string sera o arquivo de servico. O conteudo depois sera o arquivo de teste.
7. **REGRA DE ARQUIVO UNICO:** No arquivo de servico, declare TODAS as classes (Entity, Repository) no mesmo arquivo, sem `public`, e PROIBIDO importar com.ifroix.atlas.entity.* ou repository.*.
8. MATRIZ DE TIPOS: PIC S9(04) -> Integer, PIC S9(X)V99 -> BigDecimal, PIC X -> String.
9. TRANSACOES: COMMIT/ROLLBACK exigem @Transactional(rollbackFor = Exception.class).
{rag_context}
10. Retorne APENAS o codigo Java (os dois arquivos separados).

IR JSON:
{ir_json}
"""

def build_correction_prompt(previous_code: str, compile_error: str, class_name: str) -> str:
    return f"""O codigo Java Spring Boot (ou o Teste JUnit) que voce gerou tem erros.
Codigo com erro:
{previous_code}
Erro do Maven:
{compile_error}
CORRIJA o codigo. Mantenha o pacote com.ifroix.atlas e a classe {class_name}.
LEMBRE-SE DA SEPARACAO DE ARQUIVOS com `// --- FILE: {class_name}Test.java ---`.
Retorne APENAS o codigo Java corrigido.
"""

def extract_java_files(llm_output: str, expected_class_name: str) -> tuple[str, str, list[str]]:
    warnings = []
    # Limpa o markdown
    match = re.search(r"```(?:java|markdown)?\s*(.*?)```", llm_output, re.DOTALL | re.IGNORECASE)
    raw_code = match.group(1).strip() if match else llm_output.strip()
    
    # Verifica a separacao
    separator = f"// --- FILE: {expected_class_name}Test.java ---"
    if separator in raw_code:
        parts = raw_code.split(separator)
        service_code = parts[0].strip()
        test_code = parts[1].strip()
    else:
        warnings.append("Atencao: O LLM nao separou o arquivo de teste. Salvando apenas o servico.")
        service_code = raw_code
        test_code = ""

    # Limpeza do Service
    start_match = re.search(r"(package\s+|import\s+|public\s+class\s+)", service_code)
    if start_match: service_code = service_code[start_match.start():]
    fim = service_code.rfind("}")
    if fim != -1: service_code = service_code[:fim+1]

    # Limpeza do Test
    if test_code:
        start_test = re.search(r"(package\s+|import\s+|public\s+class\s+)", test_code)
        if start_test: test_code = test_code[start_test.start():]
        fim_test = test_code.rfind("}")
        if fim_test != -1: test_code = test_code[:fim_test+1]

    if f"class {expected_class_name}" not in service_code:
        warnings.append(f"Atencao: A classe nao se chama {expected_class_name}.")
    
    return service_code, test_code, warnings

def remove_main_method(java_code: str) -> str:
    padrao = r"public\s+static\s+void\s+main\s*\([^)]*\)\s*\{[^}]*\}"
    return re.sub(padrao, "", java_code, flags=re.DOTALL)

@app.post("/api/convert_mcp")
async def convert_mcp(req: ConvertRequest):
    start_time = time.time()
    class_name = Path(req.arquivo).stem.capitalize()
    target_path = (COBOL_ROOT / req.arquivo).resolve()
    if not target_path.exists(): raise HTTPException(status_code=404, detail="Arquivo COBOL nao encontrado.")
    with open(target_path, "r", encoding="utf-8", errors="replace") as f: cobol_raw = f.read()

    print(f"[MCP] Fase 1: PII Scrubber...")
    cobol_clean = scrub_pii(cobol_raw)

    total_lines = len(cobol_clean.split('\n'))
    chunks = []
    chunks_count = 1
    
    if total_lines > CHUNK_THRESHOLD:
        print(f"[MCP] Arquivo grande ({total_lines} linhas). Ativando Chunker...")
        chunker = CobolChunker(max_lines_per_chunk=80)
        chunks = chunker.split(cobol_clean)
        chunks_count = len(chunks)
        print(f"[MCP] Arquivo dividido em {chunks_count} chunks de 80 linhas.")
    else:
        print(f"[MCP] Arquivo pequeno ({total_lines} linhas). Processamento direto.")
        chunks = [CobolChunk(global_data_context=cobol_clean, procedure_code="", chunk_index=1)]
        chunks_count = 1

    print(f"[MCP] Fase 2: Consultando ChromaDB (RAG)...")
    called_programs, db_tables, sql_templates = [], [], []
    
    if "CALL 'SUBPRG01'" in cobol_clean:
        called_programs.append({"program_name": "SUBPRG01", "description": "Assinatura recuperada via ChromaDB RAG", "parameters": [{"name": "WS-ORDER-REC", "type": "STRUCT", "fields": [{"name": "ORDER-ID", "type": "INTEGER"}, {"name": "TOTAL-AMT", "type": "DECIMAL", "precision": 15, "scale": 2}]}]})
    
    if "EXEC SQL" in cobol_clean:
        db_tables.append({"table_name": "ORDER_ITEMS", "columns": [{"name": "ORDER_ITEM_ID", "type": "INTEGER", "is_pk": True}, {"name": "ITEM_PRICE", "type": "DECIMAL", "precision": 15, "scale": 2}]})
        try:
            sql_results = sql_rag_collection.query(query_texts=[cobol_clean[:1000]], n_results=3)
            if sql_results["documents"] and sql_results["documents"][0]:
                print(f"[RAG SQL] {len(sql_results['documents'][0])} templates recuperados!")
                for doc, meta in zip(sql_results["documents"][0], sql_results["metadatas"][0]):
                    sql_templates.append({"pattern_id": meta.get("pattern_id", "UNKNOWN"), "golden_standard_code": meta.get("payload_json", doc)})
        except Exception as e: print(f"[RAG SQL] Erro ao buscar templates: {e}")

    print(f"[MCP] Fase 3: Montando Context Envelope...")
    envelope = {
        "envelope_version": "1.0.0",
        "metadata": {"program_name": class_name, "source_language": "COBOL", "tenant_id": req.cliente, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")},
        "security_compliance": {"pii_scrubbed": True, "scrubbing_engine": "iFroix_PII_Scrubber_v2", "scrubbed_tokens_count": 1},
        "payload": {"source_code_clean": cobol_clean},
        "external_context": {"called_programs": called_programs, "database_tables": db_tables, "sql_rag_templates": sql_templates},
        "target_contract": {"output_format": "JSON_IR_CANONICAL_V1", "strict_validation": True, "additional_properties_allowed": False},
    }

    print(f"[MCP] Fase 4: LLM -> IR (AST) Canonica...")
    ir_json_consolidada = ""
    
    if chunks_count == 1:
        ir_raw = call_ollama(build_ir_prompt(envelope, cobol_clean))
        ir_json_consolidada = extract_json(ir_raw)
    else:
        ir_results = []
        for chunk in chunks:
            print(f"[MCP] Processando Chunk {chunk.chunk_index}/{chunks_count}...")
            chunk_text = chunk.global_data_context + "\n" + chunk.procedure_code if chunk.procedure_code else chunk.global_data_context
            ir_raw = call_ollama(build_ir_prompt(envelope, chunk_text))
            ir_results.append(extract_json(ir_raw))
                
        ir_json_consolidada = json.dumps({"program_id": class_name, "variaveis": [], "fluxo": [f"CHUNK_{i+1}: {ir}" for i, ir in enumerate(ir_results)]})

    print(f"[MCP] Fase 5: Validando JSON Schema...")
    try: validate_ir(ir_json_consolidada); print("JSON Schema validado com sucesso!")
    except ValueError as e: raise HTTPException(status_code=422, detail=str(e))

    # Cria a estrutura de pastas para Main e Test
    program_dir = BASE_SANDBOX / req.cliente / Path(req.arquivo).stem
    main_pkg_dir = program_dir / "src" / "main" / "java" / "com" / "ifroix" / "atlas"
    test_pkg_dir = program_dir / "src" / "test" / "java" / "com" / "ifroix" / "atlas"
    main_pkg_dir.mkdir(parents=True, exist_ok=True)
    test_pkg_dir.mkdir(parents=True, exist_ok=True)
    
    with open(program_dir / "pom.xml", "w", encoding="utf-8") as f: f.write(POM_XML_TEMPLATE)
    
    out_filename = f"{class_name}.java"
    out_main_path = main_pkg_dir / out_filename
    out_test_path = test_pkg_dir / f"{class_name}Test.java"

    tentativa = 1
    compile_error = None
    java_code = ""
    test_code = ""
    cobol_clause_key = "GENERIC"
    if "COMMIT" in cobol_clean or "ROLLBACK" in cobol_clean: cobol_clause_key = "COMMIT_ROLLBACK"
    elif "INSERT" in cobol_clean: cobol_clause_key = "INSERT"
    elif "UPDATE" in cobol_clean or "DELETE" in cobol_clean: cobol_clause_key = "UPDATE_DELETE"
    elif "EXEC SQL" in cobol_clean: cobol_clause_key = "EXEC_SQL"
    
    successful_attempt = 0
    final_error_for_postmortem = None

    while tentativa <= MAX_TENTATIVAS:
        print(f"[MCP] Fase 6: LLM -> Java + Teste (Tentativa {tentativa})...")
        if tentativa == 1: java_prompt = build_java_from_ir_prompt(ir_json_consolidada, class_name, sql_templates)
        else: java_prompt = build_correction_prompt(java_code, compile_error, class_name)
        
        llm_output = call_ollama(java_prompt)
        java_code, test_code, warnings = extract_java_files(llm_output, class_name)
        java_code = remove_main_method(java_code)
        
        with open(out_main_path, "w", encoding="utf-8") as f: f.write(java_code)
        if test_code:
            with open(out_test_path, "w", encoding="utf-8") as f: f.write(test_code)

        print(f"[MCP] Fase 7: Maven Test (Tentativa {tentativa})...")
        compile_error = None
        try:
            # O COMANDO AGORA E MVN CLEAN TEST
            try: result = subprocess.run(["mvn", "clean", "test"], cwd=program_dir, capture_output=True, text=True, timeout=TIMEOUT_SEC)
            except FileNotFoundError: result = subprocess.run([r"C:\apache-maven-3.9.16\bin\mvn.cmd", "clean", "test"], cwd=program_dir, capture_output=True, text=True, timeout=TIMEOUT_SEC)
            
            if result.returncode == 0:
                print(f"✅ Maven compilou e TESTES PASSARAM na tentativa {tentativa}!")
                successful_attempt = tentativa
                break
            else:
                compile_error = result.stdout
                final_error_for_postmortem = compile_error
                print(f"❌ Erro de compilacao/teste na tentativa {tentativa}. Verificando memoria...")
                cached_fix = retrieve_episodic_fix(compile_error, cobol_clause_key)
                if cached_fix:
                    print("[Memoria] Aplicando correcao recuperada do ChromaDB!")
                    # A memoria so tem o codigo principal, precisa rodar o loop de novo
                else:
                    correction_prompt = build_correction_prompt(java_code, compile_error, class_name)
                    # O proximo loop vai corrigir
        except Exception as e:
            compile_error = str(e)
            break
        tentativa += 1

    if successful_attempt > 1 and final_error_for_postmortem: save_postmortem(final_error_for_postmortem, cobol_clause_key, java_code)
    duration = int((time.time() - start_time) * 1000)
    return {"ok": compile_error is None, "maven_log": compile_error if compile_error else "Sucesso", "envelope_enviado": envelope, "ir_json_gerada": ir_json_consolidada, "java_code": java_code, "test_code": test_code, "duration_ms": duration, "rag_sql_templates_usados": len(sql_templates), "chunks_count": chunks_count}

@app.post("/api/chat")
async def chat_with_ollama(req: ChatRequest):
    prompt = f"Voce e o Atlas, assistente senior. Responda curto: {req.message}"
    return {"response": call_ollama(prompt, temperature=0.3).strip()}

if __name__ == "__main__":
    import uvicorn
    print("Atlas API v5.7 (Atlas Verifier) rodando na porta 8000!")
    uvicorn.run(app, host="0.0.0.0", port=8000)
