# Triagem Inteligente de Mensagens (IA + API + Make)

Projeto do **Desafio Técnico – IA e Automação (KODIE)**. Uma API em FastAPI usa IA para classificar mensagens de clientes, e um fluxo no Make encaminha cada mensagem para o setor responsável.

## 1. Apresentação da Ideia

> ✏️ **Preencha com suas palavras.** Sugestão: conte que você já viu (ou imaginou) pequenas empresas em que uma pessoa lê cada mensagem do WhatsApp/e-mail e repassa manualmente aos setores, e que isso é lento e sujeito a erros. A ideia nasceu de querer automatizar essa triagem.

## 2. Problema Escolhido

**Caso 4.1 – Classificação de Mensagens.** Uma pequena empresa recebe diariamente dúvidas, solicitações e reclamações. Hoje alguém precisa ler tudo, identificar o assunto e encaminhar manualmente. Isso consome tempo e dificulta a organização dos atendimentos.

## 3. Solução Proposta

1. A mensagem chega ao **Make** (via webhook).
2. O Make chama a **API** (`POST /classificar`).
3. A API envia a mensagem à **IA** com um prompt estruturado.
4. A IA devolve um **JSON** com categoria, prioridade, sentimento, resumo e confiança.
5. A API **valida** o JSON e aplica regras de roteamento (setor de destino e revisão humana).
6. O Make usa a resposta para **encaminhar** a mensagem (planilha/e-mail por setor).

**Papel da IA:** interpretar o texto livre (categoria, prioridade, sentimento, resumo).
**Papel do código:** validar a saída e decidir o setor. Essa decisão é determinística, previsível e testável.

Categorias → setores: `duvida → Atendimento`, `reclamacao → SAC`, `solicitacao → Operações`, `elogio → Marketing`, `outro` ou confiança baixa → `Triagem manual` (revisão humana).

## 4. Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| IA | API da Anthropic (Claude) |
| Back-end | Python 3.12 + FastAPI + Pydantic |
| Automação | Make (e, futuramente, n8n) |
| Testes | pytest |
| Extra (opcional) | Docker / Docker Compose |

## 5. Funcionamento do Sistema

### Entrada: `POST /classificar`
```json
{
  "mensagem": "Fui cobrado duas vezes no cartão e ninguém me responde!",
  "remetente": "carlos@email.com",
  "canal": "whatsapp"
}
```
Header opcional/recomendado: `X-API-Key: <API_KEY do .env>`.

### Processamento pela IA
O prompt (`app/prompts.py`) define: papel, categorias com definições, critérios de prioridade, formato JSON obrigatório e exemplos. A mensagem do cliente vai dentro de `<mensagem_cliente>` e o prompt instrui a IA a tratá-la **apenas como dado**, o que reduz o risco de *prompt injection*. A resposta é validada com Pydantic (`ClassificacaoIA`); se vier inválida, a API tenta novamente e, se falhar, responde `502`.

### Saída
```json
{
  "categoria": "reclamacao",
  "prioridade": "alta",
  "sentimento": "negativo",
  "resumo": "Cliente relata cobrança duplicada no cartão e falta de resposta.",
  "confianca": 0.96,
  "setor_destino": "SAC",
  "requer_revisao_humana": false,
  "remetente": "carlos@email.com",
  "canal": "whatsapp",
  "mensagem_original": "Fui cobrado duas vezes no cartão e ninguém me responde!"
}
```

### Automação (Make)
Veja o passo a passo e a lista de prints em [`docs/make-guide.md`](docs/make-guide.md).

### Documentação visual
> ✏️ Adicione os prints em `docs/prints/` e referencie aqui, com uma breve descrição de cada um (fluxo completo, execução bem-sucedida, configuração de cada módulo e dados de cada etapa).

## 6. Como Executar

### Pré-requisitos
Python 3.10+ e uma chave de API da Anthropic.

### Local
```bash
git clone <url-do-seu-repositorio>
cd triagem-ia
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # edite e preencha as variáveis
uvicorn app.main:app --reload
```
Documentação interativa: http://localhost:8000/docs

### Testando com curl
```bash
curl -X POST http://localhost:8000/classificar \
  -H "Content-Type: application/json" \
  -H "X-API-Key: SUA_API_KEY" \
  -d '{"mensagem": "Qual o prazo de entrega?", "canal": "site"}'
```
Mais exemplos em `exemplos/mensagens.json`.

### Disparando mensagens de exemplo no Make
Com `MAKE_WEBHOOK_URL` definida no `.env`:
```bash
python scripts/enviar_exemplos.py              # envia todas as mensagens de exemplo
python scripts/enviar_exemplos.py --indice 1   # envia só uma
python scripts/enviar_exemplos.py --dry-run    # só mostra, sem enviar
```

### Testes automatizados
```bash
pytest
```
(Os testes não chamam a IA de verdade: usam mock.)

### Docker (opcional)
```bash
cp .env.example .env             # preencha as variáveis
docker compose up --build        # só a API
docker compose --profile n8n up  # API + n8n (http://localhost:5678)
```
Dentro do Compose, o n8n acessa a API em `http://api:8000/classificar`.

### Expondo a API para o Make
O Make roda na nuvem e **não enxerga `localhost`**. Para testar localmente, use um túnel:
```bash
ngrok http 8000      # ou: cloudflared tunnel --url http://localhost:8000
```
Use a URL pública gerada no módulo HTTP do Make. Como ela fica exposta, **mantenha o `API_KEY` configurado**.

## Estrutura do Projeto
```
app/            código da API (main, schemas, prompts, classifier, routing, config)
tests/          testes automatizados
exemplos/       mensagens de exemplo
docs/           documentação e prints do fluxo
make/           export/blueprint do cenário do Make
Dockerfile, docker-compose.yml, .env.example
```

## Segurança
- Nenhuma credencial no repositório: tudo via `.env` (ignorado pelo Git); apenas `.env.example` é versionado.
- Endpoint protegido por `X-API-Key`.
- Validação de entrada (tamanho mínimo/máximo) e de saída (enums e faixa de confiança).

## Próximos passos
- Replicar o fluxo no **n8n** (exportar o JSON em `n8n/`).
- Guardar histórico em banco de dados e medir acurácia com um conjunto de mensagens rotuladas.
