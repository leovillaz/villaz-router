# API HTTP

Esta é a referência manual canônica da API pública do Villaz Router. OpenAPI, Swagger UI e ReDoc estão desabilitados; `/openapi.json`, `/docs` e `/redoc` não são superfícies publicadas.

A URL local padrão é `http://127.0.0.1:8000`. Requests JSON devem usar `Content-Type: application/json`.

## POST /v1/prompt

Executa o fluxo determinístico Router → Dispatcher/Profile Registry e, para decisões despacháveis, solicita a geração ao Ollama.

### Request

`PromptRequest` possui exatamente estes campos:

| Campo | Tipo | Obrigatório | Contrato |
| --- | --- | :---: | --- |
| `message` | string | sim | 1 a 16.384 caracteres; não pode conter apenas whitespace |
| `explicit_profile` | string ou `null` | não | 1 a 128 caracteres quando informado; não pode conter apenas whitespace |

Campos adicionais são rejeitados. As strings são preservadas sem trim ou normalização na camada HTTP.

Request com roteamento automático:

```json
{
  "message": "Meu Rigidbody está se movimentando de forma irregular."
}
```

Request com profile explícito:

```json
{
  "message": "Revise a clareza deste documento técnico.",
  "explicit_profile": "docs-dev"
}
```

O profile explícito válido tem precedência sobre o roteamento automático. Profile inexistente ou desabilitado falha sem fallback.

### Sucesso

HTTP `200` retorna `PromptResponse` com exatamente:

| Campo | Tipo | Semântica |
| --- | --- | --- |
| `response` | string | texto devolvido pelo executor |
| `profile` | string | profile efetivamente despachado |
| `model` | string | identificador do modelo confirmado pelo resultado |
| `state` | `explicit` ou `routed` | origem da decisão despachável |
| `route_id` | string ou `null` | obrigatório para `routed` e `null` para `explicit` |

Exemplo ilustrativo de resposta roteada:

```json
{
  "response": "Resposta produzida pelo modelo.",
  "profile": "unity-dev",
  "model": "qwen2.5-coder:14b",
  "state": "routed",
  "route_id": "ROUTE-UNITY-001"
}
```

Exemplo ilustrativo de resposta explícita:

```json
{
  "response": "Resposta produzida pelo modelo.",
  "profile": "docs-dev",
  "model": "gemma3:12b",
  "state": "explicit",
  "route_id": null
}
```

O texto gerado pode variar. A resposta pública não inclui system prompt, regras, hashes, scoring, `DispatchPlan` nem payload bruto do Ollama.

## Estados de roteamento

Os quatro estados do Router são públicos como semântica:

- `explicit` e `routed` seguem para Dispatcher e Ollama;
- `ambiguous` termina com HTTP 409 e não executa Ollama;
- `unrouted` termina com HTTP 422 e não executa Ollama.

Não há fallback silencioso.

## Erros de roteamento

### Rota ambígua

HTTP `409`:

```json
{
  "error": {
    "code": "AMBIGUOUS_ROUTE",
    "message": "The request matches multiple routes.",
    "candidates": [
      {
        "route_id": "ROUTE-UNITY-001",
        "profile": "unity-dev",
        "comparison_score": 10
      },
      {
        "route_id": "ROUTE-MOBILE-001",
        "profile": "mobile-dev",
        "comparison_score": 10
      }
    ]
  }
}
```

A ordem de `candidates` é a ordem produzida pela decisão do Router.

### Request sem rota

HTTP `422`:

```json
{
  "error": {
    "code": "UNROUTED",
    "message": "The request could not be routed."
  }
}
```

### Profile explícito inválido ou desabilitado

HTTP `422`:

```json
{
  "error": {
    "code": "INVALID_PROFILE",
    "message": "The explicit profile is invalid or disabled."
  }
}
```

## Validação HTTP

JSON inválido, tipos incorretos, campos extras, strings vazias ou compostas somente por whitespace e violações dos limites de campo retornam HTTP `422` no formato padrão de validação do FastAPI:

```json
{
  "detail": [
    {
      "loc": ["body", "campo"],
      "msg": "descrição da validação",
      "type": "tipo_da_validacao"
    }
  ]
}
```

Os itens de `detail` podem incluir metadados adicionais e variam conforme a violação. Esse erro genérico ainda não usa o envelope `error`.

## Limite bruto do body

O limite global é contado em bytes reais dos eventos `http.request` no ASGI `receive` boundary, antes de FastAPI, Pydantic e Router:

- 65.536 bytes são permitidos;
- 65.537 bytes ou mais retornam HTTP `413`;
- `Content-Length` não é usado como autoridade.

Resposta exata:

```json
{
  "error": {
    "code": "REQUEST_TOO_LARGE",
    "message": "The request body exceeds the maximum allowed size."
  }
}
```

## Erros internos e do serviço de modelos

| Condição pública | HTTP | Mensagem |
| --- | :---: | --- |
| `INTERNAL_ERROR` | 500 | `The request could not be completed due to an internal error.` |
| `MODEL_SERVICE_TIMEOUT` | 504 | `The model service timed out.` |
| `MODEL_SERVICE_UNAVAILABLE` | 503 | `The model service is unavailable.` |
| `MODEL_SERVICE_ERROR` | 502 | `The model service failed to complete the request.` |

Formato:

```json
{
  "error": {
    "code": "MODEL_SERVICE_UNAVAILABLE",
    "message": "The model service is unavailable."
  }
}
```

O `HTTP_STATUS_ERROR` interno do Ollama é traduzido para `MODEL_SERVICE_ERROR` com HTTP 502. O status upstream não é propagado. Exceções internas, causas, configuração, modelo solicitado, system prompt e payload upstream não são expostos.

## Health endpoints

### GET /health/live

HTTP `200`:

```json
{
  "status": "alive"
}
```

Liveness não consulta o Ollama.

### GET /health/ready

Readiness verifica somente se o `RuntimeContext` e o `OllamaExecutor` válidos estão presentes no lifespan.

HTTP `200`:

```json
{
  "status": "ready"
}
```

HTTP `503` quando esse estado não está disponível:

```json
{
  "status": "not_ready"
}
```

Readiness não faz probe de rede nem verifica inventário de modelos no Ollama.
