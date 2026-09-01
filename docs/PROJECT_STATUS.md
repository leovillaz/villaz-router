# Status do projeto

## Implementação concluída

### IMPLEMENTAÇÃO-001.01

Contratos internos e invariantes básicas.

### IMPLEMENTAÇÃO-001.02

Modelos formais do ruleset.

### IMPLEMENTAÇÃO-001.03

Loader estrutural dos YAMLs.

### IMPLEMENTAÇÃO-001.04

Validação semântica e referências cruzadas.

### ROUTER-007

Reconciliação entre a especificação consolidada e o repositório:

- separação Domain × Intent preservada em Security / Code Review;
- rota `code-review-security` condicionada ao intent `review-security`;
- evidências aprovadas sincronizadas com o ruleset;
- invariantes de `RouteDecision` fortalecidas;
- validação de IDs, versões, scoring e profiles desabilitados;
- prioridades duplicadas permitidas como precedência válida;
- `minimum_score` permitido acima de uma evidência `strong`;
- matriz RT-001–RT-048 versionada como contrato de regressão.

## Validação atual

```text
893 passed in 2.43s
```

A suíte corrente comprova Router, execução comportamental integral de RT-001–RT-048, Profile Registry, Dispatcher, Runtime Compatibility Validator, configuração operacional oficial, Application Bootstrap determinístico e o fluxo vertical HTTP → Router → Dispatcher/Profile Registry → Ollama Execution → HTTP. O gate terminou sem failures, skips, xfails, warnings do pytest ou erros de collection. Os checkpoints históricos mantêm seus respectivos totais de testes nas seções abaixo.



Ruleset oficial:

```text
profiles: 5
domains: 4
intents: 4
routes: 5
regression cases: 48
```

## IMPLEMENTAÇÃO-001.05 — concluída

Implementado:

- canonicalização semântica;
- JSON determinístico UTF-8;
- SHA-256 lógico;
- `RulesetSnapshot`;
- inclusão de `RouterSettings` no snapshot;
- integração do snapshot ao loader;
- independência da ordem física das coleções YAML;
- validação de formato hexadecimal SHA-256.

Hash lógico do ruleset oficial `1.0.0` neste checkpoint:

```text
ee57b50c8ff5f15476276610b6850c30509933e129a7a43062159348e0cbe575
```

Suíte vigente naquele checkpoint:

```text
66 passed
```

## IMPLEMENTAÇÃO-001.06 — concluída tecnicamente

Implementado:

- normalização determinística com NFKC, `casefold()`, remoção de diacríticos e colapso de whitespace;
- preservação de pontuação;
- `EvidenceMatch` Pydantic congelado e estrito;
- matching de `phrase` por substring literal contínua;
- matching de `term` com fronteiras formais Unicode/número/`_`;
- primeira ocorrência válida por evidência;
- matching agregado imutável ordenado por `evidence_id`;
- normalização simétrica de mensagem e `evidence.value`;
- rejeição semântica fail-fast de evidência que normalize para vazio;
- APIs públicas `normalize_text`, `match_evidence`, `match_evidence_set` e `EvidenceMatch`.

Suíte vigente ao fechamento técnico:

```text
97 passed
```

## IMPLEMENTAÇÃO-001.07 — concluída

Implementado:

- modelos públicos `EvidenceContribution` e `ScoringResult`;
- invariant estrutural `score == soma dos weights`;
- código `INVALID_SCORING_INPUT`;
- scoring configurável por `ScoringConfig`;
- associação determinística `EvidenceMatch` → `Evidence` por `evidence_id`;
- validação de IDs duplicados, referências desconhecidas e divergências de tipo/valor;
- ordem fail-fast determinística;
- contribuições canonicalizadas por `evidence_id`;
- suporte a iteráveis e generators;
- API pública `score_evidence_matches`.

Suíte vigente ao fechamento técnico:

```text
124 passed
```

## IMPLEMENTAÇÃO-001.08 — concluída tecnicamente

Implementado:

- modelo público e imutável `RouteCandidate`;
- evolução de `RouteDecision` com `route_id` e `comparison_score`;
- elegibilidade por `minimum_score`;
- weak-only gate em runtime;
- avaliação determinística de Domains e Intents;
- qualificação estrutural de Routes;
- `comparison_score` transitório sem soma Domain + Intent;
- gate de conflito entre múltiplos Intents `route_capable`;
- precedência por maior `priority`;
- resolução por `minimum_margin`;
- empate no topo tratado como ambiguidade;
- candidatos ambíguos ordenados por `comparison_score` DESC e `route_id` ASC;
- precedência absoluta de `explicit_profile`;
- perfil explícito inválido ou desabilitado retornando `INVALID_PROFILE`, sem fallback;
- mapeamento determinístico de `RoutingReason`;
- semântica de `conflict_resolved`;
- estados finais `explicit`, `routed`, `ambiguous` e `unrouted`;
- API pública `decide_route`.

Suíte vigente ao fechamento técnico:

```text
180 passed
```

## VALIDAÇÃO-001.09 — concluída tecnicamente

Validado:

- executor comportamental de RT-001–RT-048 contra `decide_route()`;
- 48 casos executados com sucesso;
- RT-045–RT-048 executados 10 vezes cada conforme contrato de determinismo;
- `RT-015` e `RT-032` reconciliados em `conflict_resolved=false`, preservando mensagem, perfil, reason e ruleset;
- divergências classificadas como inconsistência da matriz normativa, não erro de implementação ou ruleset;
- suíte completa ao fechamento técnico: `228 passed`;
- `git diff --check` aprovado.

## IMPLEMENTAÇÃO-002.02 — Profile Registry — concluída tecnicamente

Implementado e validado:

- domínio de erros próprio com `RegistryErrorCode` e `RegistryError`;
- `ProfileDefinition` imutável com IDs canônicos e strings obrigatórias sem normalização destrutiva;
- `ProfileRegistrySnapshot` imutável, ordenado e com `profile_ids` derivados;
- resolução exata por `get()`, `contains()` e `list_profiles()`;
- canonicalização lógica independente da ordem física do YAML;
- `registry_hash` SHA-256 determinístico conforme contrato aprovado;
- loader próprio de `profiles/profiles.yaml`, sem reutilizar helpers privados do Router;
- tradução de falhas em `INVALID_REGISTRY`, `INVALID_PROFILE_DEFINITION` e `DUPLICATE_PROFILE_ID`;
- cobertura integrada loader → definição → canonicalização → snapshot;
- exports públicos do Profile Registry pelo pacote `villaz_router`;
- suíte completa no fechamento técnico: `333 passed`;
- `git diff --check` aprovado.

Observação histórica deste checkpoint: o arquivo operacional oficial `profiles/profiles.yaml` ainda não havia sido criado. Essa pendência foi resolvida posteriormente na IMPLEMENTAÇÃO-002.06.

## IMPLEMENTAÇÃO-002.04 — Dispatcher — concluída e publicada

Implementado e validado:

- domínio próprio `DispatcherErrorCode` / `DispatcherError`;
- modelo imutável `DispatchPlan` com validação de estado, `route_id`, hash e campos obrigatórios;
- API pura `build_dispatch_plan(decision, registry)`;
- suporte somente aos estados `routed` e `explicit`;
- rejeição imediata de `ambiguous` e `unrouted`, sem consulta ao Registry;
- resolução exata do perfil pelo Profile Registry;
- tradução exclusiva de `RegistryErrorCode.PROFILE_NOT_FOUND` para o domínio do Dispatcher, preservando `__cause__`;
- perfil desabilitado tratado como erro, sem fallback;
- `ValidationError` do `DispatchPlan` convertido somente na fronteira final para `INVALID_DISPATCH_PLAN`;
- exceções inesperadas e erros não relacionados do Registry não são mascarados;
- exports públicos `build_dispatch_plan`, `DispatchPlan`, `DispatcherError` e `DispatcherErrorCode`;
- direção de dependências protegida: Router + Registry → Dispatcher;
- testes específicos do Dispatcher: `51 passed`;
- suíte completa no fechamento técnico: `384 passed`;
- `git diff --check` aprovado.

O Dispatcher foi publicado no commit `0d86e74f696519e8944a8129e3ab83be47409e67`.

## IMPLEMENTAÇÃO-002.05 — Runtime Compatibility Validator — concluída e publicada

Implementado e validado:

- API pura `validate_runtime_compatibility(ruleset, registry)`;
- validação determinística de referências de Routes;
- compatibilidade 1:1 entre os catálogos do Router e do Registry;
- validação do estado `enabled`;
- domínio independente `RuntimeCompatibilityError`;
- razões estruturadas e ordem fail-fast determinística;
- nenhuma dependência de Dispatcher, loaders, filesystem, FastAPI, Ollama ou rede;
- suíte completa ao fechamento: `411 passed`;
- commit publicado: `9ce02487ab7adaee6bb4de70755da04d66af23a7`.

## IMPLEMENTAÇÃO-002.06 — Configuração operacional dos Profiles — concluída e publicada

Implementado e validado:

- `profiles/profiles.yaml` oficial;
- cinco profiles operacionais, todos habilitados;
- `ProfileDefinition.system_prompt` como fonte normativa do comportamento;
- modelos base executáveis registrados em `ProfileDefinition.model`;
- aliases especializados do Ollama sem autoridade normativa;
- catálogo Router ↔ Registry validado em compatibilidade 1:1;
- `registry_hash` oficial: `c9b7ef321815b11f6a38fcd0c4b3538bc549e78a41a1149760e3c49f8dcbf6af`;
- teste integrado da configuração operacional oficial;
- suíte completa ao fechamento: `412 passed`;
- commit publicado: `cc87f0b79380f77c3dafd8804b5e547e9580538a`.

## IMPLEMENTAÇÃO-002.07 — Application Bootstrap — concluída e publicada

Implementado e validado:

- API pública síncrona `bootstrap_runtime(configuration_root)`;
- raiz explícita, obrigatória, absoluta e validada;
- sequência determinística Ruleset → Profile Registry → Runtime Compatibility → `RuntimeContext`;
- `RuntimeContext` imutável com exatamente a raiz e os snapshots aprovados;
- domínio próprio `ApplicationBootstrapError`;
- estágios e códigos estruturados, com causa original preservada;
- interrupção na primeira falha, sem retry, fallback ou estado parcial;
- erros inesperados não são mascarados;
- ausência de estado global e de I/O durante importação;
- independência de FastAPI, HTTP, ASGI, Ollama e rede;
- exports públicos do bootstrap;
- teste integrado com a configuração operacional oficial;
- 23 novos testes;
- suíte completa no fechamento: `435 passed`;
- commit publicado: `77643dbd2b7d624f6929514e4858bbd1c0e36cb9`.
- `git diff --check` aprovado.

## IMPLEMENTAÇÃO-002.08 — FastAPI Application Shell e Lifecycle — concluída tecnicamente

Implementado e validado localmente:

- adaptador HTTP isolado em `villaz_router.http_api`;
- API pública `create_app(configuration_root)` sem argumento padrão;
- factory sem bootstrap, I/O ou singleton global;
- lifespan moderno executando `bootstrap_runtime()` uma vez por ciclo;
- `RuntimeContext` publicado por identidade em `app.state.runtime_context`;
- remoção do contexto em `finally` após o encerramento;
- API pública e tipada `get_runtime_context(request)`;
- invariants explícitas para contexto ausente ou de tipo incorreto;
- endpoints públicos mínimos `GET /health/live` e `GET /health/ready`;
- respostas exatas e sem exposição de configuração operacional;
- OpenAPI, Swagger UI e ReDoc desabilitados;
- startup fail-fast, sem retry, fallback ou estado parcial;
- proteção da direção FastAPI → Application Bootstrap → domínio;
- ausência de dependência HTTP no núcleo publicado;
- ausência de Uvicorn, Ollama, Dispatcher em runtime HTTP e endpoint funcional de prompts;
- dependências fixadas em FastAPI `0.141.1` e HTTPX2 `2.12.0`;
- `pip check` sem requisitos quebrados;
- 45 novos testes unitários, arquiteturais e integrados;
- suíte completa corrente: `480 passed`;
- `git diff --check` aprovado.

Os resultados acima constituem o fechamento técnico desta etapa.

## IMPLEMENTAÇÃO-002.09 — Ollama Execution — concluída tecnicamente localmente

Implementado e validado localmente:

- subpacote isolado `villaz_router.ollama_execution`;
- configuração explícita e imutável por `OllamaClientConfig`, `OllamaTimeoutConfig` e `OllamaConnectionLimits`;
- request e result próprios por `OllamaExecutionRequest` e `OllamaExecutionResult`;
- domínio próprio e estruturado de erros de execução e transporte;
- protocolo assíncrono e injetável `OllamaTransport`;
- `OllamaExecutor` assíncrono com lifecycle próprio e fechamento idempotente;
- payload exato para `POST /api/generate`;
- uso exclusivo de `DispatchPlan.model`, `DispatchPlan.system_prompt` e `OllamaExecutionRequest.user_prompt`;
- preservação da separação entre system prompt e prompt do usuário;
- `stream=false`, `raw=false` e `think=false`;
- ausência de fallback, retry, preflight, heartbeat, inventário, preload, pull ou download de modelos;
- ausência de logging, telemetria, persistência, shell ou subprocessos na camada;
- implementação concreta interna `Httpx2OllamaTransport`;
- HTTPX2 `2.12.0` como dependência de runtime;
- AnyIO `4.14.2` como dependência de desenvolvimento/teste;
- HTTP/1.1 habilitado e HTTP/2 desabilitado;
- `trust_env=False`;
- redirects desabilitados;
- retries igual a zero;
- limites explícitos de conexão e keep-alive;
- factory pública `create_ollama_executor(config)` sem rede durante construção;
- superfície pública exata do subpacote Ollama Execution;
- ausência de símbolos Ollama no pacote raiz `villaz_router`;
- ausência de dependência Ollama no Router, Dispatcher, Application Bootstrap e FastAPI Application Shell;
- proteção arquitetural contra endpoints adicionais além de `/api/generate`;
- teste integrado oficial Bootstrap → Router → Dispatcher/Profile Registry → Ollama Execution;
- uso do caso normativo `RT-017` no teste de integração;
- transporte falso utilizado no fluxo integrado, sem TCP, servidor Ollama, GPU ou internet;
- teste isolado oficial do fluxo integrado aprovado com `1 passed`.

No checkpoint histórico da IMPLEMENTAÇÃO-002.09, a integração HTTP funcional ainda não fazia parte do escopo e o FastAPI Application Shell permanecia sem endpoint de prompts. Essa pendência foi resolvida posteriormente na IMPLEMENTAÇÃO-002.10.

A suíte completa da IMPLEMENTAÇÃO-002.09 foi aprovada com `707 passed` em `2.07s`, baseline histórico substituído pelo gate da IMPLEMENTAÇÃO-002.10.

O fechamento documental, `compileall`, `pip check`, testes específicos, suíte completa, revisão final de diff e publicação Git pertencem ao Bloco 7 desta implementação.

## IMPLEMENTAÇÃO-002.10 — HTTP Functional Prompt Execution — concluída tecnicamente localmente

Implementado e validado localmente:

- configuração oficial `config/ollama.yaml` e loader dedicado;
- bootstrap do `RuntimeContext` e criação de um único `OllamaExecutor` no lifespan;
- executor armazenado em `app.state`, reutilizado entre requests e fechado no shutdown;
- startup sem probe de rede Ollama;
- readiness dependente de `RuntimeContext` e `OllamaExecutor` válidos, sem probe externo;
- limite bruto global no ASGI `receive` boundary, antes de FastAPI/Pydantic/Router, permitindo 65.536 bytes e rejeitando 65.537 bytes com HTTP 413 e `REQUEST_TOO_LARGE`;
- adapter HTTP–Router sem dependência de Dispatcher, Ollama ou response objects do FastAPI;
- endpoint funcional `POST /v1/prompt`;
- composição Router → Dispatcher/Profile Registry → `OllamaExecutionRequest` → `OllamaExecutor`;
- estados `explicit` e `routed` despachados; estado `AMBIGUOUS` → HTTP 409, `UNROUTED` → HTTP 422 e `INVALID_PROFILE` → HTTP 422;
- mapeamento seguro em `INTERNAL_ERROR` → HTTP 500, `MODEL_SERVICE_TIMEOUT` → HTTP 504, `MODEL_SERVICE_UNAVAILABLE` → HTTP 503 e `MODEL_SERVICE_ERROR` → HTTP 502, sem exposição de detalhes sensíveis;
- `HTTP_STATUS_ERROR` do Ollama traduzido para `MODEL_SERVICE_ERROR` → HTTP 502, sem propagação do status upstream;
- propagação de `asyncio.CancelledError` preservada;
- integração vertical hermética de RT-017/Unity pela API HTTP, substituindo somente o boundary final do Ollama;
- suíte automatizada sem necessidade de rede ou servidor Ollama real;
- gate completo aprovado com `893 passed in 2.43s`, sem failures, skips, xfails, warnings do pytest ou erros de collection.

O estado é tecnicamente concluído localmente. Commit, push e publicação da IMPLEMENTAÇÃO-002.10 ainda não foram realizados.

## Próxima etapa

- executar o Public Release Hardening;
- concluir o gate Git e de publicação.

## Ainda não implementado

- autenticação e autorização;
- servidor ASGI e deployment;
- Orchestrator;
- Villaz CLI / Villaz Terminal.
