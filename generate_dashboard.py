import sqlite3
import json
import os

DB_PATH = "./atlas.db"
OUTPUT_FILE = "dashboard_gtm.html"

def generate_dashboard():
    if not os.path.exists(DB_PATH):
        print("❌ Banco atlas.db não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Puxa os dados brutos
    cursor.execute("SELECT program_name, status, attempts, duration_seconds, chunks_count FROM conversion_audit ORDER BY id ASC")
    rows = cursor.fetchall()
    
    programs = []
    durations = []
    chunks = []
    
    total = len(rows)
    success_1st = 0
    success_healing = 0
    failed = 0
    total_duration = 0
    total_chunks = 0

    for row in rows:
        programs.append(row["program_name"])
        durations.append(row["duration_seconds"])
        chunks.append(row["chunks_count"])
        
        total_duration += row["duration_seconds"]
        total_chunks += row["chunks_count"]
        
        if row["status"] == "SUCCESS":
            if row["attempts"] == 1:
                success_1st += 1
            else:
                success_healing += 1
        else:
            failed += 1

    avg_time = total_duration / total if total > 0 else 0
    success_rate = (success_1st / total * 100) if total > 0 else 0

    conn.close()

    # 2. Monta o HTML (Dark Mode Enterprise)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Atlas Agentic - Dashboard GTM v5.6</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{ --bg: #0f172a; --panel: #1e293b; --text: #f8fafc; --accent: #38bdf8; --success: #22c55e; --warning: #f59e0b; --danger: #ef4444; }}
            body {{ background-color: var(--bg); color: var(--text); font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ margin: 0; color: var(--accent); }}
            .header p {{ color: #94a3b8; }}
            .kpi-container {{ display: flex; justify-content: space-around; margin-bottom: 40px; flex-wrap: wrap; gap: 20px; }}
            .kpi-card {{ background: var(--panel); padding: 20px; border-radius: 12px; text-align: center; width: 200px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-top: 4px solid var(--accent); }}
            .kpi-card h3 {{ margin: 0; font-size: 14px; color: #94a3b8; text-transform: uppercase; }}
            .kpi-card .value {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
            .chart-container {{ background: var(--panel); padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); height: 400px; display: flex; justify-content: center; }}
            .charts-row {{ display: flex; gap: 20px; flex-wrap: wrap; }}
            .chart-box {{ flex: 1; min-width: 300px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Atlas Agentic - Dashboard GTM</h1>
            <p>Relatório Executivo de Conversão de Legado (v5.6)</p>
        </div>

        <div class="kpi-container">
            <div class="kpi-card">
                <h3>Total de Programas</h3>
                <div class="value" style="color: var(--accent);">{total}</div>
            </div>
            <div class="kpi-card" style="border-top-color: var(--success);">
                <h3>Taxa de Sucesso</h3>
                <div class="value" style="color: var(--success);">{success_rate:.1f}%</div>
            </div>
            <div class="kpi-card" style="border-top-color: var(--warning);">
                <h3>Tempo Médio</h3>
                <div class="value" style="color: var(--warning);">{avg_time:.1f}s</div>
            </div>
            <div class="kpi-card">
                <h3>Total de Chunks</h3>
                <div class="value" style="color: var(--text);">{total_chunks}</div>
            </div>
        </div>

        <div class="charts-row">
            <div class="chart-container chart-box">
                <canvas id="statusChart"></canvas>
            </div>
            <div class="chart-container chart-box">
                <canvas id="timeChart"></canvas>
            </div>
        </div>

        <script>
            const programs = {json.dumps(programs)};
            const durations = {json.dumps(durations)};
            const chunksData = {json.dumps(chunks)};

            // Gráfico de Pizza (Status)
            const ctx1 = document.getElementById('statusChart').getContext('2d');
            new Chart(ctx1, {{
                type: 'doughnut',
                data: {{
                    labels: ['1ª Tentativa', 'Auto-Correção', 'Falhas'],
                    datasets: [{{
                        data: [{success_1st}, {success_healing}, {failed}],
                        backgroundColor: ['#22c55e', '#f59e0b', '#ef4444'],
                        borderWidth: 1
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#f8fafc' }} }} }} }}
            }});

            // Gráfico de Barras (Tempo por Programa)
            const ctx2 = document.getElementById('timeChart').getContext('2d');
            new Chart(ctx2, {{
                type: 'bar',
                data: {{
                    labels: programs,
                    datasets: [{{
                        label: 'Tempo (s)',
                        data: durations,
                        backgroundColor: '#38bdf8',
                        borderRadius: 4
                    }}]
                }},
                options: {{ 
                    responsive: true, 
                    maintainAspectRatio: false,
                    scales: {{ 
                        y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#334155' }} }},
                        x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ display: false }} }}
                    }},
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Dashboard gerado com sucesso! Abra o arquivo: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_dashboard()
