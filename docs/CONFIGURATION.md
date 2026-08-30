# Configuração do Router

Arquivo:

```text
config/router.yaml
```

Configuração oficial v1:

```yaml
schema_version: "1.0"

router:
  engine:
    expected_major_version: 1

  scoring:
    strong: 10
    medium: 4
    weak: 1

  eligibility:
    minimum_score: 10
    weak_only_cannot_qualify: true

  ambiguity:
    minimum_margin: 5

  normalization:
    unicode_nfkc: true
    lowercase: true
    lowercase_locale_independent: true
    collapse_whitespace: true
    accent_insensitive_matching: true

  lifecycle:
    ruleset_reload: startup_only
    immutable_snapshot_per_instance: true

  integrity:
    algorithm: sha256
    canonical_format: deterministic_json_utf8

  privacy:
    store_full_message: false
    store_evidence: true
```

## Scoring

| Strength | Pontos |
|---|---:|
| strong | 10 |
| medium | 4 |
| weak | 1 |

## Elegibilidade

`minimum_score = 10`

`minimum_score` é um threshold agregado de elegibilidade. Ele pode ser configurado com valor superior ao peso de uma única evidência `strong`, permitindo exigir corroboração por múltiplas evidências.

A relação obrigatória entre os pesos é `strong > medium > weak`.

Evidências exclusivamente `weak` não podem tornar um candidato elegível, mesmo se a soma atingir o threshold.

## Ambiguidade

`minimum_margin = 5`

A margem é aplicada apenas depois das precedências semânticas.

## Lifecycle

Não há hot reload no Router v1.

## Integridade

A identidade lógica do ruleset está implementada como SHA-256 sobre representação canônica em JSON determinístico UTF-8.

A canonicalização inclui:

- configuração efetiva do Router;
- profiles;
- domains;
- intents;
- routes.

Coleções semanticamente não ordenadas são ordenadas por `id` antes da serialização. Evidências também são ordenadas por `id` dentro de cada domain ou intent.

Portanto, mudanças de comentários, espaçamento, formatação ou ordem física dos itens nos YAMLs não alteram o hash lógico. Mudanças semânticas alteram o hash.

O JSON canônico usa:

- UTF-8;
- chaves ordenadas;
- separadores compactos;
- caracteres Unicode preservados;
- rejeição de valores numéricos não JSON como `NaN`.

O `RulesetSnapshot` inclui o hash lógico, a configuração efetiva do Router e todas as estruturas do ruleset em ordem canônica.

## Configuração da Ollama Execution

A camada `villaz_router.ollama_execution` possui configuração própria e explícita por meio de três modelos imutáveis:

- `OllamaClientConfig`;
- `OllamaTimeoutConfig`;
- `OllamaConnectionLimits`.

Nenhum desses modelos define valores default. Todos os campos necessários devem ser informados explicitamente pela camada que construir o executor.

### `OllamaClientConfig`

Campos obrigatórios:

- `base_url`: URL base do servidor Ollama;
- `timeouts`: instância de `OllamaTimeoutConfig`;
- `limits`: instância de `OllamaConnectionLimits`.

`base_url` aceita somente os esquemas `http` e `https` e deve conter um host válido.

A URL não pode conter:

- credenciais embutidas;
- query string;
- fragment;
- whitespace;
- caminho de operação.

Assim, a URL representa somente a raiz do servidor. O endpoint operacional `/api/generate` é responsabilidade interna do transporte.

### `OllamaTimeoutConfig`

Campos obrigatórios:

- `connect_seconds`;
- `read_seconds`;
- `write_seconds`;
- `pool_seconds`.

Todos devem ser valores `float` estritos, finitos e maiores que zero.

### `OllamaConnectionLimits`

Campos obrigatórios:

- `max_connections`;
- `max_keepalive_connections`;
- `keepalive_expiry_seconds`.

Regras:

- `max_connections` deve ser inteiro estrito maior que zero;
- `max_keepalive_connections` deve ser inteiro estrito maior ou igual a zero;
- `max_keepalive_connections` não pode exceder `max_connections`;
- `keepalive_expiry_seconds` deve ser `float` estrito, finito e maior que zero.

### Factory oficial

`create_ollama_executor(config)` transforma a configuração em um `OllamaExecutor` usando HTTPX2.

A factory configura explicitamente:

- HTTP/1.1 habilitado;
- HTTP/2 desabilitado;
- `trust_env=False`;
- redirects desabilitados;
- retries igual a zero;
- timeouts explícitos;
- limites explícitos de conexão.

A criação do executor não realiza conexão de rede. A rede somente pode ser utilizada posteriormente durante uma chamada explícita de execução.

A configuração da Ollama Execution não pertence a `config/router.yaml` e não altera o ruleset determinístico.
