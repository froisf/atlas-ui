import requests
import time
import concurrent.futures
import random
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
API_URL = "http://127.0.0.1:8000/api/convert_mcp"
HEALTH_URL = "http://127.0.0.1:8000/docs"

COBOL_ROOT = Path(r"D:\Workspace\01-Products\nw-poc\legacy-cobol")
TEST_FILES = ["a.cbl", "cfc018.cbl", "insert.cbl", "update.cbl", "select.cbl"]

# Configurações do K8s para monitoramento do HPA (Novo, mas não quebra nada se falhar)
K8S_NAMESPACE = "atlas-agentic"
K8S_DEPLOYMENT = "atlas-core"


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def check_hpa_status():
    """Consulta o status atual do HPA no Kubernetes. Falha silenciosa se for local."""
    try:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "hpa",
                f"{K8S_DEPLOYMENT}-hpa",
                "-n",
                K8S_NAMESPACE,
                "-o",
                "json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        hpa_data = json.loads(result.stdout)
        current = hpa_data["status"].get("currentReplicas", 1)
        desired = hpa_data["status"].get("desiredReplicas", 1)
        return f"📈 Pods K8s: {current}/{desired}"
    except Exception:
        return "⚠️ K8s/HPA não acessível (Provavelmente rodando em Modo Local)"


def health_check():
    print(f"🔍 Verificando saúde do servidor em {HEALTH_URL}...")
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Servidor está no ar e pronto.")
            print(f"   Status do Cluster: {check_hpa_status()}")
            return True
    except requests.exceptions.ConnectionError:
        print(
            "❌ ERRO: O servidor não está rodando. Inicie o 'python api_bridge.py' ou verifique o K8s."
        )
        return False
    except Exception as e:
        print(f"⚠️ Aviso no health check: {e}")
    return False


def send_conversion_request(file_name, timeout_sec=60, delay_between_requests=0):
    """Envia uma requisição e mede o tempo de resposta."""
    if delay_between_requests > 0:
        time.sleep(delay_between_requests)

    start_time = time.time()
    try:
        response = requests.post(
            API_URL,
            json={"arquivo": file_name, "cliente": "LOAD_TEST_GTM"},
            timeout=timeout_sec,  # Melhoria: falha rápida em vez de travar por 30min
        )
        duration = time.time() - start_time

        if response.status_code == 200:
            dados = response.json()
            risk = dados.get("risk_level", "UNKNOWN")
            status = "SUCCESS" if dados.get("ok") else "FAILED"
            return {
                "file": file_name,
                "status": status,
                "risk": risk,
                "duration": round(duration, 2),
                "job_id": dados.get("job_id"),
            }
        else:
            return {
                "file": file_name,
                "status": f"HTTP_{response.status_code}",
                "duration": round(duration, 2),
            }
    except Exception as e:
        return {
            "file": file_name,
            "status": "ERROR",
            "error": str(e),
            "duration": round(time.time() - start_time, 2),
        }


def run_load_test(concurrent_workers=1, total_requests=10, timeout_sec=60, delay=0):
    print(
        f"\n🚀 INICIANDO TESTE DE CARGA: {total_requests} reqs | Workers: {concurrent_workers} | Delay: {delay}s"
    )
    print("-" * 60)

    start_total = time.time()
    tasks = [random.choice(TEST_FILES) for _ in range(total_requests)]
    results = []

    print("⏳ Disparando carga e monitorando HPA...")

    # PRESERVADO: Sua lógica original de Sequencial vs Paralelo
    if concurrent_workers <= 1:
        # Modo Sequencial (recomendado para máquinas locais)
        for i, task in enumerate(tasks):
            print(f"[{i+1}/{total_requests}] Processando {task}...")
            res = send_conversion_request(
                task, timeout_sec=timeout_sec, delay_between_requests=delay
            )
            results.append(res)

            # Monitora HPA a cada 20% mesmo no modo sequencial
            if (i + 1) % max(1, total_requests // 5) == 0:
                print(f"   [{time.time() - start_total:05.1f}s] {check_hpa_status()}")
    else:
        # Modo Paralelo (usar em K8s)
        print(f"⚠️ Modo Paralelo: Requisições serão disparadas simultaneamente.")
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=concurrent_workers
        ) as executor:
            future_to_file = {
                executor.submit(send_conversion_request, task, timeout_sec, delay): task
                for task in tasks
            }

            total_done = 0
            for future in concurrent.futures.as_completed(future_to_file):
                results.append(future.result())
                total_done += 1

                if total_done % max(1, total_requests // 5) == 0:
                    elapsed = time.time() - start_total
                    print(
                        f"   [{elapsed:05.1f}s] {total_done}/{total_requests} concluídas | {check_hpa_status()}"
                    )

    total_time = time.time() - start_total

    print("\n⏳ Aguardando 10s para observar o início do scale-down do K8s...")
    time.sleep(10)
    print(f"   Status Final: {check_hpa_status()}")

    # ==============================================================================
    # RELATÓRIO FINAL (Lógica original preservada, apenas com nome de arquivo dinâmico)
    # ==============================================================================
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DO TESTE DE CARGA (GTM READY)")
    print("=" * 60)
    success = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    errors = sum(
        1
        for r in results
        if r["status"] in ["ERROR", "HTTP_500", "HTTP_502", "HTTP_503", "HTTP_504"]
    )

    print(f"Total de Requisições: {total_requests}")
    print(f"✅ Sucessos:          {success} ({(success/total_requests)*100:.1f}%)")
    print(f"❌ Falhas de Lógica:  {failed}")
    print(f"💥 Erros de Servidor: {errors}")
    print(f"⏱️ Tempo Total:       {total_time:.2f}s")
    print(f"⚡ Throughput:        {(total_requests/total_time):.2f} req/seg")
    print("=" * 60)

    report = {
        "timestamp": datetime.now().isoformat(),
        "workers": concurrent_workers,
        "total_requests": total_requests,
        "total_time": round(total_time, 2),
        "hpa_final_status": check_hpa_status(),
        "results": results,
    }

    # Melhoria de segurança: nome dinâmico para não sobrescrever testes anteriores
    report_filename = (
        f"load_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print(f"📄 Relatório salvo em: {report_filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Atlas Agentic Load Test (GTM Edition)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Número de workers paralelos (default: 1)",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=2,
        help="Número total de requisições (default: 2)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0,
        help="Delay entre requisições em segundos (default: 0)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout por requisição em segundos (default: 60)",
    )

    args = parser.parse_args()

    if health_check():
        run_load_test(
            concurrent_workers=args.workers,
            total_requests=args.requests,
            timeout_sec=args.timeout,
            delay=args.delay,
        )
    else:
        print("❌ Teste abortado. Certifique-se de que o servidor está rodando.")
