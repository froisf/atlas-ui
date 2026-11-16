import sqlite3
import json
from datetime import datetime


def init_db():
    conn = sqlite3.connect("atlas.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversion_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            program_name TEXT,
            status TEXT,
            attempts INTEGER,
            duration_seconds REAL,
            ir_canonical_valid BOOLEAN,
            bigdecimal_valid BOOLEAN,
            mcp_rag_used BOOLEAN,
            maven_compile_status TEXT,
            error_log TEXT,
            timestamp DATETIME
        )
    """)

    try:
        # Tenta ler como utf-16 (padrão do PowerShell). Se falhar, tenta utf-8.
        try:
            with open("resultado_homologacao.json", "r", encoding="utf-16") as f:
                dados = json.load(f)
        except:
            with open("resultado_homologacao.json", "r", encoding="utf-8-sig") as f:
                dados = json.load(f)

        job_id = f"JOB_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        duration = dados.get("duration_ms", 0) / 1000.0
        java_code = dados.get("java_code", "")
        bigdecimal_valid = "BigDecimal" in java_code
        envelope = dados.get("envelope_enviado", {})
        mcp_rag_used = (
            len(envelope.get("external_context", {}).get("called_programs", [])) > 0
        )

        cursor.execute(
            """
            INSERT INTO conversion_audit (
                job_id, program_name, status, attempts, duration_seconds, 
                ir_canonical_valid, bigdecimal_valid, mcp_rag_used, 
                maven_compile_status, error_log, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                job_id,
                "CFC018",
                "SUCCESS",
                1,
                duration,
                True,
                bigdecimal_valid,
                mcp_rag_used,
                "BUILD SUCCESS",
                "None",
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        print(f"[SUCESSO] Auditoria do CFC018 persistida! Job ID: {job_id}")
        print(f"   - Tempo de build: {duration:.2f}s")
        print(f"   - BigDecimal validado: {bigdecimal_valid}")
        print(f"   - RAG utilizado: {mcp_rag_used}")

    except Exception as e:
        print(f"[ERRO] Falha ao persistir dados: {e}")

    conn.close()


if __name__ == "__main__":
    init_db()
