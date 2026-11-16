import requests
from pathlib import Path
import time
import json
import os

API_URL = "http://127.0.0.1:8000/api/convert_mcp"
COBOL_ROOT = Path(r"D:\Workspace\01-Products\nw-poc\legacy-cobol")
BATCH_RESULTS_DIR = Path(os.getcwd()) / "batch_results"


def run_batch():
    BATCH_RESULTS_DIR.mkdir(exist_ok=True)

    # CORREÇÃO: Filtra todos os arquivos e remove duplicatas ignorando maiúsculas/minúsculas
    unique_files = {}
    for f in COBOL_ROOT.glob("*"):
        if f.suffix.lower() == ".cbl":
            unique_files[f.name.lower()] = f

    cobol_files = sorted(list(unique_files.values()), key=lambda x: x.name.lower())
    total_arquivos = len(cobol_files)

    if total_arquivos == 0:
        print("Nenhum arquivo COBOL encontrado.")
        return

    print(f"Iniciando lote de {total_arquivos} arquivos UNICOS na esteira MCP...")

    stats = {"sucesso_1a": 0, "sucesso_autocorrecao": 0, "falha": 0}

    for idx, file in enumerate(cobol_files, 1):
        filename = file.name
        print(f"[{idx}/{total_arquivos}] Processando {filename}...", end="", flush=True)

        try:
            res = requests.post(API_URL, json={"arquivo": filename}, timeout=1200)

            if res.status_code == 200:
                dados = res.json()

                with open(
                    BATCH_RESULTS_DIR / f"{filename}.json", "w", encoding="utf-8"
                ) as f:
                    json.dump(dados, f, indent=2)

                if dados.get("ok"):
                    if dados.get("tentativas", 1) == 1:
                        print(f" [OK] 1a Tentativa")
                        stats["sucesso_1a"] += 1
                    else:
                        print(f" [OK] Auto-Correcao ({dados.get('tentativas')}x)")
                        stats["sucesso_autocorrecao"] += 1
                else:
                    print(f" [FALHA] Erro de Compilacao")
                    stats["falha"] += 1
            else:
                print(f" [ERRO API] HTTP {res.status_code}: {res.text[:50]}")
                stats["falha"] += 1

        except Exception as e:
            print(f" [ERRO CONEXAO] {str(e)}")
            stats["falha"] += 1

    print("\n" + "=" * 50)
    print("RELATORIO FINAL")
    print("=" * 50)
    print(f"Sucesso 1a Tentativa: {stats['sucesso_1a']}")
    print(f"Sucesso com Auto-Correcao: {stats['sucesso_autocorrecao']}")
    print(f"Falhas: {stats['falha']}")
    print("=" * 50)


if __name__ == "__main__":
    run_batch()
