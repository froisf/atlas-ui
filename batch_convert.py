import requests
import time
from pathlib import Path
from datetime import datetime

# Configurações
API_URL = "http://127.0.0.1:8000/api/convert"
COBOL_ROOT = Path(r"D:\Workspace\01-Products\nw-poc\legacy-cobol")

def formatar_tempo(segundos):
    minutos = int(segundos // 60)
    seg = int(segundos % 60)
    return f"{minutos}m {seg}s" if minutos > 0 else f"{seg}s"

def run_batch():
    cobol_files = sorted(list(COBOL_ROOT.glob("*.cbl")) + list(COBOL_ROOT.glob("*.CBL")))
    total_arquivos = len(cobol_files)
    
    if total_arquivos == 0:
        print("❌ Nenhum arquivo COBOL encontrado.")
        return

    hora_inicio = datetime.now()
    print("=" * 60)
    print("🚀 MIGRAÇÃO EM MASSA - ATLAS AGENTIC")
    print("=" * 60)
    print(f"📂 Pasta: {COBOL_ROOT}")
    print(f"📊 Programas encontrados: {total_arquivos}")
    print(f"⏱️  Hora de Início: {hora_inicio.strftime('%H:%M:%S')}")
    print("-" * 60)

    stats = {"sucesso_1a": 0, "sucesso_autocorrecao": 0, "falha": 0}
    tempo_inicio_loop = time.time()
    
    for idx, file in enumerate(cobol_files, 1):
        filename = file.name
        progresso = f"[{idx}/{total_arquivos}] Processando {filename:<20}"
        print(f"\r{progresso}", end="", flush=True)
        
        try:
            res = requests.post(API_URL, json={"arquivo": filename}, timeout=300)
            
            if res.status_code == 200:
                dados = res.json()
                tentativas = dados.get("tentativas", 1)
                erro = dados.get("compile_error")
                
                if erro:
                    stats["falha"] += 1
                    print(f"\r❌ [{idx}/{total_arquivos}] {filename:<20} (Falhou)")
                elif tentativas == 1:
                    stats["sucesso_1a"] += 1
                else:
                    stats["sucesso_autocorrecao"] += 1
            else:
                stats["falha"] += 1
                print(f"\r❌ [{idx}/{total_arquivos}] {filename:<20} (Erro API)")
                
        except Exception as e:
            stats["falha"] += 1
            print(f"\r❌ [{idx}/{total_arquivos}] {filename:<20} (Erro Conexão)")

    hora_fim = datetime.now()
    tempo_total = time.time() - tempo_inicio_loop
    
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL DA MIGRAÇÃO")
    print("=" * 60)
    print(f"⏱️  Hora de Término: {hora_fim.strftime('%H:%M:%S')}")
    print(f"⏳ Tempo Total Gasto: {formatar_tempo(tempo_total)}")
    print("-" * 60)
    print(f"✅ Sucesso de primeira:       {stats['sucesso_1a']} arquivos")
    print(f"🟡 Sucesso com auto-correção: {stats['sucesso_autocorrecao']} arquivos")
    print(f"❌ Falhas:                    {stats['falha']} arquivos")
    print("=" * 60)

if __name__ == "__main__":
    run_batch()
