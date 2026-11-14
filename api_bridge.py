from flask import Flask, request, jsonify, send_from_directory
import subprocess
import requests
import re

app = Flask(__name__, static_folder='.')

historico_conversa = [
    {"role": "system", "content": "Você é o Atlas Agentic, um assistente de engenharia de software da iFroix. A iFroix foca na conversão de código legado (COBOL e RPG/RPGLE) para Java 21. Você é educado, direto e focado em ajudar o Tech Lead Flavio Frois com o pipeline de modernização."}
]

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/convert', methods=['POST'])
def convert():
    return jsonify({
        "status": "success",
        "steps": [
            {"nome": "1. Ingestão", "detalhe": "15 arquivos lidos.", "status": "green"},
            {"nome": "2. Orquestração", "detalhe": "Atlas assumiu o pipeline.", "status": "green"},
            {"nome": "3. Geração (GenerateAST)", "detalhe": "Traduzindo para Java 21...", "status": "orange"},
            {"nome": "4. Conferência (ConfereAST)", "detalhe": "Aguardando geração.", "status": "grey"},
            {"nome": "5. Entrega", "detalhe": "Aguardando validação.", "status": "grey"}
        ]
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    global historico_conversa
    dados = request.json
    mensagem = dados.get('message', '')
    
    palavras_chave = ["converter", "conversão", "cbl", "rpgle", "rpg", "rodar", "pipeline"]
    if any(palavra in mensagem.lower() for palavra in palavras_chave):
        
        match = re.search(r'([a-zA-Z0-9_-]+\.(sqlrpgle|rpgle|rpg|cbl))', mensagem, re.IGNORECASE)
        
        if not match:
            resposta = "Entendido! Qual é o nome do arquivo que você deseja converter? (Ex: CFC018.rpgle)"
            historico_conversa.append({"role": "assistant", "content": resposta})
            return jsonify({"response": resposta})
            
        caminho_arquivo = match.group(1)
        
        pasta_poc = r"D:\Workspace\01-Products\mega-rag-clean"
        script_atual = r"rpgle_chunker.py" 
        
        try:
            resultado = subprocess.run(
                ["python", script_atual, caminho_arquivo],
                cwd=pasta_poc, capture_output=True, text=True, check=True, encoding='utf-8'
            )
            
            if resultado.stdout.strip() == "":
                texto_saida = "O script executou sem erros, mas não retornou texto no terminal."
            else:
                texto_saida = resultado.stdout.strip()
            
            resposta = f"🚀 **Conversão do arquivo {caminho_arquivo} iniciada!**\n\nResultado do pipeline:\n```\n{texto_saida}\n```"
            
            historico_conversa.append({"role": "user", "content": mensagem})
            historico_conversa.append({"role": "assistant", "content": resposta})
            
            return jsonify({"response": resposta})
            
        except subprocess.CalledProcessError as e:
            erro_msg = f"❌ **Erro ao converter {caminho_arquivo}:**\n```\n{e.stderr.strip()}\n```"
            return jsonify({"response": erro_msg})
        except Exception as e:
            return jsonify({"response": f"❌ Erro inesperado: {str(e)}"})

    historico_conversa.append({"role": "user", "content": mensagem})
    
    if len(historico_conversa) > 7:
        historico_conversa = [historico_conversa[0]] + historico_conversa[-6:]

    try:
        res = requests.post('http://localhost:11434/api/chat', json={
            "model": "llama3.2:3b", 
            "messages": historico_conversa,
            "stream": False
        }, timeout=120) 
        
        retorno_ollama = res.json()
        
        if 'error' in retorno_ollama:
            return jsonify({"response": f"O Ollama retornou um erro: {retorno_ollama['error']}"})
            
        resposta_ia = retorno_ollama.get('message', {}).get('content', 'O Ollama não devolveu texto.')
        historico_conversa.append({"role": "assistant", "content": resposta_ia})
        
        return jsonify({"response": resposta_ia.strip()})
        
    except Exception as e:
        return jsonify({"response": f"Erro de conexão com o Ollama: {str(e)}. O Ollama está aberto?"})

if __name__ == '__main__':
    print("API Bridge rodando em http://localhost:8000")
    app.run(port=8000, debug=True)
