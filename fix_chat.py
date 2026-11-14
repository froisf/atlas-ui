import re

file_path = 'index.html'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Encontra o setTimeout que contém a palavra "assistant"
    padrao = re.compile(r'window\.setTimeout\(.*?role:"assistant".*?\},\s*\d+\)', re.DOTALL)
    
    substituicao = 'fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: O }) }).then(res => res.json()).then(dados => { let sd = {id:++wr, role:"assistant", text: dados.response}; x(y.id, [sd]); k(!1); }).catch(erro => { let sd = {id:++wr, role:"assistant", text: "Erro no MCP: " + erro.message}; x(y.id, [sd]); k(!1); });'

    novo_html, num = padrao.subn(substituicao, html)

    if num > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(novo_html)
        print(f"✅ SUCESSO! O chat foi alterado ({num} substituicao(oes)).")
    else:
        print("⚠️ Nao foi possivel encontrar o codigo do chat neste HTML.")
except FileNotFoundError:
    print("Erro: index.html nao encontrado.")
