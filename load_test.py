import requests
import time
import concurrent.futures
import random
import json
import argparse
from pathlib import Path
from datetime import datetime

API_URL = "http://127.0.0.1:8000/api/convert_mcp"
HEALTH_URL = "http://127.0.0.1:8000/api/chat"  # Usamos o chat como health check simples
COBOL_ROOT = Path(r"D:\Workspace\01-Products\nw-poc\legacy-cobol")

# Lista de arquivos para testar (misturando LOW e HIGH risk)
TEST_FILES = ["a.cbl", "cfc018.cbl", "insert.cbl", "update.cbl", "select.cbl"]

def health_check():
    """Verifica se o servidor está no ar antes de iniciar o teste."""
    print(f"🔍 Verificando saúde do servidor em {API_URL}...")
    try:
        # Tenta acessar a rota de chat (ou qualquer rota que responda rápido)
        response = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor está no ar e pronto para receber requisições.")
            return True
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: O servidor não está rodando. Inicie o 'python api_bridge.py' primeiro.")
        return False
    except Exception as e:
        print(f"⚠️ Aviso no health check: {e}")
    return False

def send_conversion_request(file_name, delay_between_requests=0):
    """Envia uma requisição e mede o tempo de resposta."""
    if delay_between_requests > 0:
        time.sleep(delay_between_requests)

    start_time = time.time()
    try:
        response = requests.post(
            API_URL, 
            json={"arquivo": file_name, "cliente": "LOAD_TEST"},
            timeout=1800 
        )
        duration = time.time() - start_time
        
        if response.status_code == 200:
            dados = response.json()
            risk = dados.get("risk_level", "UNKNOWN")
            status = "SUCCESS" if dados.get("ok") else "FAILED"
            result = {
                "file": file_name,
                "status": status,
                "risk": risk,
                "duration": round(duration, 2),
                "job_id": dados.get("job_id")
            }
            print(f"  [{file_name}] -> Status: {status} | Risk: {risk} | Tempo: {duration:.2f}s")
            return result
        else:
            result = {"file": file_name, "status": f"HTTP_{response.status_code}", "duration": round(duration, 2)}
            print(f"  [{file_name}] -> HTTP {response.status_code} | Tempo: {duration:.2f}s")
            return result
    except Exception as e:
        result = {"file": file_name, "status": "ERROR", "error": str(e), "duration": round(time.time() - start_time, 2)}
        print(f"  [{file_name}] -> ERRO: {str(e)}")
        return result

def run_load_test(concurrent_workers=1, total_requests=2, delay=0):
    print(f"\n🚀 Iniciando Teste de Carga: {total_requests} requisições | Workers: {concurrent_workers} | Delay: {delay}s\n")
    start_total = time.time()
    
    tasks = [random.choice(TEST_FILES) for _ in range(total_requests)]
    results = []
    
    if concurrent_workers <= 1:
        # Modo Sequencial (recomendado para máquinas locais)
        for i, task in enumerate(tasks):
            print(f"[{i+1}/{total_requests}] Processando {task}...")
            res = send_conversion_request(task, delay_between_requests=delay)
            results.append(res)
    else:
        # Modo Paralelo (usar apenas em K8s com GPUs)
        print(f"⚠️ Modo Paralelo: Requisições serão disparadas simultaneamente.")
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
            results = list(executor.map(lambda f: send_conversion_request(f, delay), tasks))
    
    total_time = time.time() - start_total
    
    print("\n" + "="*50)
    print("📊 RELATÓRIO FINAL DO TESTE DE CARGA")
    print("="*50)
    success = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    errors = sum(1 for r in results if r["status"] in ["ERROR", "HTTP_500", "HTTP_502"])
    
    print(f"Total de Requisições: {total_requests}")
    print(f"✅ Sucessos: {success}")
    print(f"❌ Falhas de Lógica: {failed}")
    print(f"💥 Erros de Conexão/Servidor: {errors}")
    print(f"⏱️ Tempo Total: {total_time:.2f}s")
    print("="*50)

    # Salva o relatório em JSON
    report = {
        "timestamp": datetime.now().isoformat(),
        "workers": concurrent_workers,
        "total_requests": total_requests,
        "total_time": round(total_time, 2),
        "results": results
    }
    with open("load_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print("📄 Relatório salvo em 'load_test_report.json'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Atlas Agentic Load Test")
    parser.add_argument("--workers", type=int, default=1, help="Número de workers paralelos (default: 1)")
    parser.add_argument("--requests", type=int, default=2, help="Número total de requisições (default: 2)")
    parser.add_argument("--delay", type=float, default=0, help="Delay entre requisições em segundos (default: 0)")
    
    args = parser.parse_args()
    
    if health_check():
        run_load_test(concurrent_workers=args.workers, total_requests=args.requests, delay=args.delay)
    else:
        print("❌ Teste abortado. Certifique-se de que o 'python api_bridge.py' está rodando.")
