import os
import hmac
import hashlib
import requests
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
WEBHOOK_SECRET = os.getenv("ATLAS_WEBHOOK_SECRET", "secret_key_prod_v52")

class CommitAuthor(BaseModel):
    name: str
    email: str

class Commit(BaseModel):
    id: str
    message: str
    author: CommitAuthor
    added: List[str] = []
    modified: List[str] = []

def verify_signature(payload_bytes: bytes, signature_header: Optional[str]):
    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Assinatura HMAC ausente ou malformada.")
    
    expected_hash = hmac.new(
        WEBHOOK_SECRET.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    received_hash = signature_header.split("sha256=")[1]
    
    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(status_code=403, detail="Assinatura HMAC invalida.")

def trigger_mcp_pipeline_task(file_path: str):
    print(f"[BG TASK] Disparando esteira MCP para: {file_path}")
    try:
        requests.post("http://127.0.0.1:8000/api/convert_mcp", 
                      json={"arquivo": file_path, "cliente": "WEBHOOK_GIT"}, 
                      timeout=1200)
        print(f"[BG TASK] Finalizado: {file_path}")
    except Exception as e:
        print(f"[BG TASK] Erro ao processar {file_path}: {e}")

@router.post("/github")
async def handle_github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: Optional[str] = Header(None)
):
    payload_bytes = await request.body()
    verify_signature(payload_bytes, x_hub_signature_256)
    
    payload = await request.json()
    
    target_files = set()
    for commit in payload.get("commits", []):
        for filepath in commit.get("added", []) + commit.get("modified", []):
            if filepath.lower().endswith(('.cbl', '.cob', '.rpgle')):
                target_files.add(filepath)
    
    if not target_files:
        return {"status": "ignored", "reason": "Nenhum arquivo legado alterado."}
    
    for file_path in target_files:
        background_tasks.add_task(trigger_mcp_pipeline_task, file_path)
        
    return {
        "status": "queued",
        "processed_files": list(target_files),
        "total_jobs": len(target_files)
    }
