# Guia do cenário no Make

Cenário: **Webhook → Create JSON → HTTP → Router → (Planilha / E-mail)**

> Os nomes de módulos podem variar levemente conforme a versão da interface do Make.

## Pré-requisitos
- API rodando e acessível publicamente (ngrok, cloudflared ou deploy). Veja o README.
- Conta no Make (plano gratuito serve).
- Uma Google Sheets com abas: `Atendimento`, `SAC`, `Operações`, `Marketing`, `Triagem manual`. Cabeçalho sugerido: `data | remetente | canal | categoria | prioridade | sentimento | resumo | mensagem`.

## Módulos

### 1. Webhooks > Custom webhook
- Crie um webhook e copie a URL.
- Envie um teste para ele **e depois clique em "Re-determine data structure"** para o Make aprender os campos:
```bash
curl -X POST "URL_DO_WEBHOOK" -H "Content-Type: application/json" \
  -d '{"mensagem":"Fui cobrado duas vezes no cartão!","remetente":"carlos@email.com","canal":"whatsapp"}'
```

### 2. JSON > Create JSON
- Crie uma *data structure* com 3 campos de texto: `mensagem`, `remetente`, `canal`.
- Mapeie os valores vindos do webhook.
- **Por quê?** Se você montar o JSON na mão, aspas ou quebras de linha na mensagem do cliente quebram o corpo da requisição. Este módulo faz o escape corretamente.

### 3. HTTP > Make a request
- **URL:** `https://SEU-TUNEL/classificar`
- **Method:** POST
- **Headers:** `X-API-Key: <seu API_KEY>` (use o mesmo valor do `.env`)
- **Body type:** Raw / **Content type:** JSON (application/json)
- **Request content:** a saída (JSON string) do módulo 2
- Marque **Parse response** (para os campos da resposta ficarem disponíveis nos próximos módulos).
- Marque **Evaluate all states as errors** (para tratar 4xx/5xx como erro).

### 4. Flow Control > Router
Crie as rotas com filtros sobre os campos da resposta da API:

| Rota | Filtro |
|---|---|
| Revisão humana | `requer_revisao_humana` = `true` |
| Atendimento | `setor_destino` = `Atendimento` **e** `requer_revisao_humana` = `false` |
| SAC | `setor_destino` = `SAC` **e** `requer_revisao_humana` = `false` |
| Operações | `setor_destino` = `Operações` **e** `requer_revisao_humana` = `false` |
| Marketing | `setor_destino` = `Marketing` **e** `requer_revisao_humana` = `false` |

### 5. Ações de cada rota
- **Google Sheets > Add a Row** na aba do setor correspondente, mapeando os campos da resposta da API.
- (Opcional) **Gmail/Email > Send an Email** quando `prioridade` = `alta`, avisando o responsável do setor.

## Testando
1. No Make, clique em **Run once**.
2. Envie as mensagens de `exemplos/mensagens.json` ao webhook, uma por vez.
3. Confira se cada uma caiu na aba certa.

## Prints obrigatórios (salvar em `docs/prints/`)
1. **Fluxo completo**: todos os módulos conectados.
2. **Execução bem-sucedida**: histórico de execução com status OK.
3. **Configuração de cada módulo**: Webhook, Create JSON, HTTP, Router (e filtros), Sheets/E-mail.
4. **Resultados**: dados de entrada e saída de cada etapa importante (clique na bolha de cada módulo após o *Run once*).
5. **Bônus**: resultado final na planilha e a documentação da API em `/docs`.

Exporte o cenário (**⋯ > Export Blueprint**) e salve em `make/` (confira que não há chaves ou tokens no arquivo antes de commitar).
