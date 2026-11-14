import re

file_path = 'index.html'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # O Regex procura por "window.setTimeout" e captura tudo até o ", 650)"
    padrao = re.compile(r'window\.setTimeout\(\(\)=>\{.*?\},\s*\d+\)', re.DOTALL)
    
    substituicao = 'fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: O }) }).then(res => res.json()).then(dados => { let sd = {id:++wr, role:"assistant", text: dados.response}; x(y.id, [sd]); k(!1); }).catch(erro => { let sd = {id:++wr, role:"assistant", text: "Erro no MCP: " + erro.message}; x(y.id, [sd]); k(!1); });'

    novo_html, num_substituicoes = padrao.subn(substituicao, html)

    if num_substituicoes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(novo_html)
        print(f"✅ SUCESSO! O HTML foi alterado ({num_substituicoes} substituicao(oes) feita(s)).")
    else:
        print("⚠️ O padrao do setTimeout nao foi encontrado. O arquivo pode ser muito diferente.")

except FileNotFoundError:
    print("Erro: index.html nao encontrado.")
