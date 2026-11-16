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

    cursor.execute("SELECT program_name, status, attempts, duration_seconds, chunks_count, risk_level, approval_status FROM conversion_audit ORDER BY id ASC")
    rows = cursor.fetchall()
    
    programs = []
    durations = []
    chunks = []
    
    total = len(rows)
    success_1st = 0
    failed = 0
    auto_approved = 0
    pending_approval = 0
    approved = 0

    for row in rows:
        programs.append(row["program_name"])
        durations.append(row["duration_seconds"])
        chunks.append(row["chunks_count"])
        
        if row["status"] == "SUCCESS":
            success_1st += 1
        else:
            failed += 1
            
        if row["approval_status"] == "AUTO_APPROVED": auto_approved += 1
        elif row["approval_status"] == "PENDING": pending_approval += 1
        elif row["approval_status"] == "APPROVED": approved += 1

    avg_time = sum(durations) / total if total > 0 else 0
    success_rate = (success_1st / total * 100) if total > 0 else 0

    conn.close()

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Atlas Agentic - Dashboard GTM v6.1</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root {{ --bg: #0f172a; --panel: #1e293b; --text: #f8fafc; --accent: #38bdf8; --success: #22c55e; --warning: #f59e0b; --danger: #ef4444; }}
            body {{ background-color: var(--bg); color: var(--text); font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .header h1 {{ margin: 0; color: var(--accent); }}
            .kpi-container {{ display: flex; justify-content: space-around; margin-bottom: 40px; flex-wrap: wrap; gap: 20px; }}
            .kpi-card {{ background: var(--panel); padding: 20px; border-radius: 12px; text-align: center; width: 200px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-top: 4px solid var(--accent); }}
            .kpi-card h3 {{ margin: 0; font-size: 14px; color: #94a3b8; text-transform: uppercase; }}
            .kpi-card .value {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
            .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .chart-box {{ background: var(--panel); padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); height: 350px; }}
            @media (max-width: 768px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Atlas Super Agentic - Dashboard GTM</h1>
            <p>Relatório Executivo de Conversão e Governança (v6.1)</p>
        </div>

        <div class="kpi-container">
            <div class="kpi-card">
                <h3>Total Convertido</h3>
                <div class="value" style="color: var(--accent);">{total}</div>
            </div>
            <div class="kpi-card" style="border-top-color: var(--success);">
                <h3>Taxa de Sucesso</h3>
                <div class="value" style="color: var(--success);">{success_rate:.1f}%</div>
            </div>
            <div class="kpi-card" style="border-top-color: var(--warning);">
                <h3>Tempo Médio</h3>
                <div class="value" style="color: var(--warning);">{avg_time:.0f}s</div>
            </div>
            <div class="kpi-card">
                <h3>Chunks Processados</h3>
                <div class="value" style="color: var(--text);">{sum(chunks)}</div>
            </div>
        </div>

        <div class="charts-grid">
            <div class="chart-box">
                <canvas id="riskChart"></canvas>
            </div>
            <div class="chart-box">
                <canvas id="approvalChart"></canvas>
            </div>
        </div>

        <script>
            // Gráfico de Rosca: Aprovação
            new Chart(document.getElementById('approvalChart').getContext('2d'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Auto-Aprovado (LOW)', 'Pendente (HIGH)', 'Aprovado (Humano)'],
                    datasets: [{{
                        data: [{auto_approved}, {pending_approval}, {approved}],
                        backgroundColor: ['#22c55e', '#f59e0b', '#38bdf8'],
                        borderWidth: 1
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#f8fafc' }} }}, title: {{ display: true, text: 'Governança & Approval Gate', color: '#f8fafc' }} }} }}
            }});
            
            // Gráfico de Barras: Tempo por Programa
            new Chart(document.getElementById('riskChart').getContext('2d'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(programs)},
                    datasets: [{{
                        label: 'Tempo de Conversão (s)',
                        data: {json.dumps(durations)},
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
                    plugins: {{ legend: {{ display: false }}, title: {{ display: true, text: 'Performance por Programa', color: '#f8fafc' }} }}
                }}
            }});
        </script>
    </body>
    </html>
    """

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Dashboard v6.1 gerado com sucesso! Abra o arquivo: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_dashboard()
