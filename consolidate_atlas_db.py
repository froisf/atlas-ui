import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = "./atlas.db"
RESULTS_DIR = Path("batch_results")

def upgrade_schema(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(conversion_audit)")
    columns = [col[1] for col in cursor.fetchall()]
    
    new_columns = {
        "chunks_count": "INTEGER DEFAULT 1",
        "payload_tokens_approx": "INTEGER DEFAULT 0",
        "start_time": "TEXT",
        "finish_time": "TEXT",
        "artifact_path": "TEXT"
    }
    
    for col_name, col_type in new_columns.items():
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE conversion_audit ADD COLUMN {col_name} {col_type}")
                print(f"[OK] Coluna {col_name} adicionada ao schema.")
            except Exception as e:
                print(f"[AVISO] Erro ao adicionar {col_name}: {e}")
    conn.commit()
    conn.close()

def consolidate_batch():
    upgrade_schema()
    if not RESULTS_DIR.exists():
        print("❌ Pasta 'batch_results' nao encontrada. Rode o batch primeiro.")
        return

    json_files = list(RESULTS_DIR.glob("*.json"))
    print(f"📊 Consolidando {len(json_files)} arquivos no atlas.db...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for file in json_files:
        with open(file, 'r', encoding='utf-8') as f:
            try:
                dados = json.load(f)
            except:
                continue
            
            program_name = file.stem.replace('.cbl', '').replace('.CBL', '')
            job_id = f"JOB_{program_name}_v5.6"
            duration = dados.get('duration_ms', 0) / 1000.0
            java_code = dados.get('java_code', '')
            bigdecimal_valid = "BigDecimal" in java_code
            
            # Métricas de Chunking (TASK-5.4.3)
            chunks_count = dados.get('chunks_count', 1)
            payload_tokens_approx = len(java_code) // 4 if java_code else 0 # Estimativa simples
            
            envelope = dados.get('envelope_enviado', {})
            mcp_rag_used = len(envelope.get('external_context', {}).get('called_programs', [])) > 0
            
            status = "SUCCESS" if dados.get('ok') else "FAILED"
            tentativas = dados.get('tentativas', 1)
            maven_status = dados.get('maven_log', 'Unknown')
            
            start_time = datetime.now().isoformat()
            finish_time = start_time

            cursor.execute('''
                INSERT INTO conversion_audit (
                    job_id, program_name, status, attempts, duration_seconds, 
                    ir_canonical_valid, bigdecimal_valid, mcp_rag_used, 
                    maven_compile_status, error_log, timestamp,
                    chunks_count, payload_tokens_approx, start_time, finish_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_id, program_name, status, tentativas, duration,
                True, bigdecimal_valid, mcp_rag_used,
                maven_status, 'None', datetime.now().isoformat(),
                chunks_count, payload_tokens_approx, start_time, finish_time
            ))
            
    conn.commit()
    conn.close()
    print("✅ Consolidação concluída! O atlas.db está pronto para o GTM.")

def generate_gtm_summary():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN attempts = 1 THEN 1 ELSE 0 END) as success_1st,
            SUM(CASE WHEN attempts > 1 THEN 1 ELSE 0 END) as success_healing,
            SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failures,
            SUM(chunks_count) as total_chunks,
            SUM(payload_tokens_approx) as total_tokens,
            AVG(duration_seconds) as avg_duration
        FROM conversion_audit
        WHERE job_id LIKE '%v5.6%'
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    total = result[0] or 1
    print("\n" + "="*50)
    print("📊 RESUMO EXECUTIVO - ATLAS GTM v5.6")
    print("="*50)
    print(f"Total de Programas:          {result[0]}")
    print(f"Sucesso 1ª Tentativa:        {result[1]} ({(result[1]/total)*100:.1f}%)")
    print(f"Sucesso c/ Auto-Correção:    {result[2]}")
    print(f"Falhas:                      {result[3]}")
    print(f"Total de Chunks Processados: {result[4]}")
    print(f"Estimativa de Tokens:        {result[5]}")
    print(f"Tempo Médio por Programa:    {result[6]:.2f}s")
    print("="*50)

if __name__ == "__main__":
    consolidate_batch()
    generate_gtm_summary()
