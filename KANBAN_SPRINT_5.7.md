# 📋 KANBAN - ATLAS AGENTIC (Atualizado em 16/11/2026 19:52)
**Regra de Ouro:** Single Source of Truth para o time.

---

## 🟢 SPRINT 5.4 (CONCLUÍDO - 100%)
- [x] **TASK-5.4.1:** RAG SQL v2 (Entity/Repository/Transactional)
- [x] **TASK-5.4.2:** CobolChunker (Fatiamento de 80 linhas) + Resilience Harness (Timeout 1800s)
- [x] **TASK-5.4.3:** Consolidação de Métricas no `atlas.db`

## 🟢 SPRINT 5.5 (CONCLUÍDO - 100%)
- [x] **TASK-5.5.1:** Atlas Verifier (JUnit 5 puro + `mvn clean test`)
- [x] **TASK-5.5.2:** Trava `failIfNoTests` no Maven e Regra de Imports no Prompt.

## 🟢 SPRINT 5.6 (CONCLUÍDO - 100%)
- [x] **TASK-5.6.1:** Risk Engine (Classificação LOW/MEDIUM/HIGH)
- [x] **TASK-5.6.2:** Approval Gate (Human-in-the-Loop via API)
- [x] **TASK-5.6.3:** Auditoria de Aprovação no `atlas.db` e `check_audit.py`
- [x] **TASK-5.6.4:** Dashboard GTM v6.1 com gráficos de Governança (Risk & Approval)
- [x] **TASK-5.6.5:** Relatório de Handover Técnico e Roteiro Executivo de Apresentação

---

## 🟡 SPRINT 5.7 (EM ANDAMENTO - GTM & Infraestrutura)
**Objetivo:** Empacotar o produto para vendas e preparar a infraestrutura para produção.

- [ ] **TASK-5.7.1 (GTM):** Validar visualmente o `dashboard_gtm.html` e alinhar os gráficos com o Roteiro Executivo do Vitruvius. Preparar o Slide Deck final.
- [ ] **TASK-5.7.2 (Infra):** Criar o `Dockerfile` e o `docker-compose.yml` para empacotar a API (FastAPI), o Ollama (ou vLLM) e o ChromaDB.
- [ ] **TASK-5.7.3 (Infra):** Desenhar os manifestos Kubernetes (Deployment, Service, ConfigMap) para deploy On-Premises na VPC do cliente.
- [ ] **TASK-5.7.4 (Infra):** Substituir o cliente Ollama local pelo cliente **vLLM** (AsyncOpenAI) preparando para GPU em nuvem.

---
*Gerado automaticamente pelo TL (Atlas Agentic)*
