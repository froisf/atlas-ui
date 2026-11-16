# 📋 SPRINT BACKLOG - ATLAS AGENTIC v5.1
**Data de Geração:** 15/11/2026
**Responsável:** Tech Lead
**Status do Motor:** Em Estabilização (Bugs identificados no Lote)

---

## 🟡 CARD 1: Sanitização do Dataset de Teste (Prioridade Alta)
- **Problema:** O lote rodou 32 arquivos, mas existiam duplicatas na pasta `legacy-cobol`. Isso sobrecarrega o servidor e polui as métricas.
- **Ação:** Limpar a pasta, deixando apenas 1 arquivo de cada. Atualizar o script de batch para ignorar duplicatas.
- **Critério de Aceite:** O lote deve rodar exatamente a quantidade de arquivos únicos.

---

## 🟡 CARD 2: Ajuste de Timeout e Tratamento de Erros 500 (Prioridade Alta)
- **Problema:** Ocorreram `Read timed out` e `HTTP 500` em arquivos grandes.
- **Ação:** Aumentar o `TIMEOUT_SEC` no `api_bridge.py` de 300 para 600s. Implementar `try/except` com retry no `batch_convert.py` para não perder o arquivo.
- **Critério de Aceite:** Nenhum arquivo deve falhar por timeout sem tentar novamente.

---

## 🟡 CARD 3: Evolução do Self-Healing (Prioridade Média)
- **Problema:** O Llama 3.2 falhou após 3 tentativas em erros complexos de sintaxe.
- **Ação:** Aumentar `MAX_TENTATIVAS` para 5. Otimizar o prompt de correção para extrair apenas a linha do erro do Maven (`[ERROR] line...`).
- **Critério de Aceite:** Aumentar a taxa de sucesso na 2ª ou 3ª tentativa.

---

## 🟡 CARD 4: Consolidação do Banco SQLite (Prioridade Alta)
- **Problema:** Precisamos dos dados reais do lote para o Dashboard do Vitruvius.
- **Ação:** Rodar o `consolidate_atlas_db.py` para jogar os resultados parciais no `atlas.db`.
- **Critério de Aceite:** Banco populado e pronto para o Dashboard GTM.

---
*Gerado automaticamente pelo Atlas Agentic*
