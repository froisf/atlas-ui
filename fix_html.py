import os

file_path = 'index.html'
if not os.path.exists(file_path):
    print("Erro: index.html nao encontrado nesta pasta.")
else:
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    target = 'window.setTimeout(()=>{let sd={id:++wr,role:"assistant",text:Pt?`Atlas Agentic entendeu: ${O}. Vou mandar GenerateAST gerar e ConfereAST conferir.\n\n${ud}`:`Atlas Agentic entendeu: ${O}. Vou mandar GenerateAST gerar e ConfereAST conferir.`};x(y.id,[sd]),k(!1)},650)'

    replacement = 'fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: O }) }).then(res => res.json()).then(dados => { let sd = {id:++wr, role:"assistant", text: dados.response}; x(y.id, [sd]); k(!1); }).catch(erro => { let sd = {id:++wr, role:"assistant", text: "Erro no MCP: " + erro.message}; x(y.id, [sd]); k(!1); });'

    if target in html:
        html = html.replace(target, replacement)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print("✅ index.html modificado com sucesso! O chat agora esta integrado.")
    else:
        print("⚠️ Trecho nao encontrado. O arquivo pode ja ter sido modificado ou e uma versao diferente.")
