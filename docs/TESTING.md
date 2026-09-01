# Testes

## Execução

```bash
.venv/bin/python -m pytest -v
```

## Estado atual

A suíte corrente possui **893 testes**, aprovados em `2.43s` sem failures, skips, xfails, warnings do pytest ou erros de collection. Permanecem preservados os baselines históricos de `228 passed` na `VALIDAÇÃO-001.09`, `333 passed` no Profile Registry, `384 passed` no Dispatcher, `411 passed` no Runtime Compatibility Validator, `412 passed` na configuração operacional oficial, `435 passed` no Application Bootstrap e `707 passed` na Ollama Execution.

Cobertura atual:

- contratos de request/decision;
- coerência entre estado, modo, razão, candidatos e conflito;
- modelos e imutabilidade do ruleset;
- leitura segura dos YAMLs oficiais;
- YAML inválido, arquivo ausente e documento não-mapping;
- IDs, versões e evidências inválidas;
- referências cruzadas;
- profiles desabilitados;
- prioridades duplicadas aceitas como precedência válida;
- coerência de scoring e threshold agregado;
- `minimum_score` superior a uma evidência `strong` aceito;
- normalização accent-insensitive na validação de duplicatas;
- associação da rota de segurança ao intent `review-security`;
- integridade do contrato RT-001–RT-048;
- execução comportamental integral de RT-001–RT-048 contra `decide_route()`;
- determinismo de RT-045–RT-048 com 10 repetições por caso;
- canonicalização determinística do ruleset;
- independência da ordem física de profiles, domains, intents, routes e evidências;
- serialização compacta em JSON UTF-8;
- mudanças semânticas alterando o hash;
- reordenação física preservando o hash;
- formato SHA-256 hexadecimal minúsculo;
- criação e estabilidade do `RulesetSnapshot`;
- inclusão das configurações do Router no snapshot;
- integração do snapshot ao loader;
- normalização NFKC + `casefold()` + accent-insensitive + whitespace;
- preservação de pontuação na representação normalizada;
- `EvidenceMatch` congelado e seus invariantes;
- matching de `phrase` por substring literal contínua;
- matching de `term` com fronteiras formais;
- primeira ocorrência válida de uma evidência;
- preservação do valor original da evidência no resultado;
- matching agregado imutável e ordenado deterministicamente por `evidence_id`;
- mensagem vazia resultando em conjunto vazio de matches;
- rejeição semântica de evidência que normalize para vazio;
- contratos e imutabilidade de `EvidenceContribution` e `ScoringResult`;
- invariant `score == soma dos weights`;
- scoring usando exclusivamente pesos de `ScoringConfig`;
- scoring vazio com `score=0` e `contributions=()`;
- independência da ordem física e suporte a generators;
- detecção determinística de IDs duplicados;
- rejeição de `EvidenceMatch` desconhecido;
- validação exata de tipo e valor entre match e evidência configurada;
- ordem fail-fast determinística dos erros de scoring;
- elegibilidade por `minimum_score`;
- weak-only gate e contribuição medium/strong;
- avaliação de todos os Domains e Intents em ordem determinística;
- qualificação estrutural de Routes e resolução exata de referências;
- exclusão de Routes desabilitadas;
- integridade defensiva de profiles;
- conflito entre múltiplos Intents `route_capable`;
- precedência por maior `priority`;
- resolução por `minimum_margin`;
- empate no maior `comparison_score`;
- faixa estrita de candidatos ambíguos;
- ordenação canônica de `RouteCandidate`;
- precedência absoluta de `explicit_profile`;
- perfil explícito inválido ou desabilitado com `INVALID_PROFILE`, sem fallback;
- estado `unrouted`;
- decisões finais `routed` e `ambiguous`;
- semântica de `conflict_resolved`;
- mapeamento determinístico de `RoutingReason`;
- exportação pública de `decide_route`;
- contratos e imutabilidade de `ProfileDefinition`;
- validação estrita de IDs, booleanos e strings obrigatórias do Profile Registry;
- contratos e imutabilidade de `ProfileRegistrySnapshot`;
- resolução exata por `get()`, `contains()` e `list_profiles()`;
- domínio próprio de erros do Registry;
- canonicalização determinística do Registry;
- ordem física de profiles no YAML sem efeito no `registry_hash`;
- alterações semânticas e whitespace válido alterando o `registry_hash`;
- serialização UTF-8 compacta sem normalização destrutiva;
- loader de `profiles/profiles.yaml` e classificação determinística de erros;
- cobertura integrada loader → definição → canonicalização → snapshot;
- exports públicos do Profile Registry.
- contratos, imutabilidade e validações de `DispatchPlan`;
- domínio próprio de erros do Dispatcher;
- construção determinística de planos para estados `routed` e `explicit`;
- rejeição de `ambiguous` e `unrouted` sem consulta ao Registry;
- tradução de `PROFILE_NOT_FOUND` preservando a causa original;
- rejeição de profiles desabilitados sem fallback;
- tradução restrita de `ValidationError` na construção final do plano;
- propagação de erros inesperados sem mascaramento;
- determinismo de `build_dispatch_plan`;
- exports públicos do Dispatcher;
- proteção da direção arquitetural Router + Registry → Dispatcher.
- domínio próprio e estruturado de erros do Runtime Compatibility Validator;
- validação de referências de Routes antes da compatibilidade dos catálogos;
- compatibilidade 1:1 entre os profiles do Ruleset e do Registry;
- validação do estado `enabled` entre Ruleset e Registry;
- ordem fail-fast determinística dos erros de compatibilidade;
- configuração operacional oficial com cinco profiles habilitados;
- modelos base e `system_prompt` canônico preservados no Profile Registry;
- `registry_hash` oficial da configuração operacional;
- contratos exatos de `BootstrapStage` e `ApplicationBootstrapErrorCode`;
- atributos, representação textual e independência de `ApplicationBootstrapError`;
- campos exatos, imutabilidade e identidade dos snapshots em `RuntimeContext`;
- raiz obrigatória, existente, diretório, legível e normalizada;
- ordem Ruleset → Registry → Runtime Compatibility → Context;
- interrupção do bootstrap na primeira falha;
- preservação de `cause` e `__cause__` dos erros especializados;
- propagação de erros inesperados sem mascaramento;
- ausência de estado global, retry, fallback e contexto parcial;
- exports públicos do Application Bootstrap;
- bootstrap integrado da configuração operacional oficial;
- independência de FastAPI, HTTP, Ollama e rede.
- contratos estritos e imutáveis de `LivenessResponse` e `ReadinessResponse`;
- factory síncrona `create_app(configuration_root)` sem bootstrap durante sua criação;
- ausência de singleton global da aplicação;
- lifespan executando o Application Bootstrap exatamente uma vez por ciclo;
- publicação e remoção do `RuntimeContext` em `app.state.runtime_context`;
- preservação da identidade do contexto;
- ciclos de lifespan e aplicações independentes;
- dependency tipada `get_runtime_context(request)`;
- erros exatos para contexto ausente ou de tipo incorreto;
- liveness independente do contexto de runtime;
- readiness dependente de `RuntimeContext` e `OllamaExecutor` válidos no lifespan, sem probe Ollama;
- respostas exatas e não sensíveis dos endpoints de health;
- rejeição de métodos inválidos e caminhos desconhecidos;
- OpenAPI, Swagger UI e ReDoc desabilitados;
- propagação de falhas de bootstrap sem mascaramento;
- proteção arquitetural FastAPI → Application Bootstrap → domínio;
- `router_adapter.py` sem dependência de Dispatcher, Ollama ou response objects do FastAPI;
- dependência de Ollama restrita a `app.py`, `dependencies.py` e `routes.py` como pontos aprovados de lifecycle, injeção e composição;
- exports públicos exatos de `villaz_router.http_api`;
- integração da aplicação FastAPI com a configuração operacional oficial;
- FastAPI `0.141.1` e HTTPX2 `2.12.0`;
- `pip check` sem requisitos quebrados;
- loader oficial de `config/ollama.yaml` e classificação de configuração inválida;
- criação única, reutilização e fechamento do `OllamaExecutor` no lifespan;
- dependencies reais de `RuntimeContext` e `OllamaExecutor`;
- limite bruto de body no ASGI `receive` boundary, antes de FastAPI/Pydantic/Router, com 65.536 bytes permitidos e 65.537 bytes rejeitados;
- preservação e replay dos eventos ASGI válidos;
- endpoint `POST /v1/prompt` e adaptação exata de `PromptRequest` para o Router;
- composição Dispatcher → `OllamaExecutionRequest` → executor;
- mapeamento público seguro: estado `AMBIGUOUS` → HTTP 409, `UNROUTED` → HTTP 422, `INVALID_PROFILE` → HTTP 422, `INTERNAL_ERROR` → HTTP 500, `MODEL_SERVICE_TIMEOUT` → HTTP 504, `MODEL_SERVICE_UNAVAILABLE` → HTTP 503 e `MODEL_SERVICE_ERROR` → HTTP 502;
- tradução de `HTTP_STATUS_ERROR` do Ollama para `MODEL_SERVICE_ERROR` → HTTP 502, sem propagação do status upstream;
- propagação de cancelamento assíncrono;
- integração vertical hermética de RT-017/Unity via HTTP, substituindo somente `OllamaExecutor.execute`.

## Cobertura da Ollama Execution

A IMPLEMENTAÇÃO-002.09 adiciona cobertura específica para a camada `villaz_router.ollama_execution`.

Os testes cobrem:

- contratos estritos e imutáveis de `OllamaTimeoutConfig`, `OllamaConnectionLimits` e `OllamaClientConfig`;
- carregamento seguro da configuração oficial por `config_loader.py`, sem rede ou criação de transporte;
- rejeição de campos extras e tipos incompatíveis;
- validação explícita de URL base, incluindo esquema, host, credenciais, query, fragment, whitespace e path operacional;
- coerência dos limites de conexão;
- contratos de `OllamaExecutionRequest` e `OllamaExecutionResult`;
- preservação por identidade do `DispatchPlan`;
- preservação exata de `model`, `system_prompt` e prompt do usuário;
- domínio próprio de erros de execução e transporte;
- protocolo assíncrono e injetável `OllamaTransport`;
- payload exato para `POST /api/generate`;
- `stream=false`, `raw=false` e `think=false`;
- tradução restrita de erros esperados;
- propagação de cancelamento e exceções inesperadas sem mascaramento;
- validação fail-fast de respostas inválidas;
- lifecycle e fechamento idempotente do executor;
- rejeição de execução após fechamento;
- transporte HTTPX2 assíncrono;
- HTTP/1.1 habilitado e HTTP/2 desabilitado;
- `trust_env=False`;
- redirects desabilitados;
- retries igual a zero;
- limites explícitos de conexão e keep-alive;
- rejeição de respostas HTTP não 2xx;
- rejeição de JSON inválido;
- factory `create_ollama_executor(config)` sem rede durante construção;
- superfície pública exata do subpacote `ollama_execution`;
- `Httpx2OllamaTransport` mantido como detalhe interno;
- ausência de símbolos Ollama no pacote raiz `villaz_router`;
- ausência de dependência Ollama no core, Dispatcher, bootstrap e `router_adapter.py`, com imports HTTP restritos aos três composition points aprovados;
- ausência de endpoints Ollama adicionais além de `/api/generate`;
- dependência HTTPX2 somente nas camadas de infraestrutura previstas;
- integração oficial Bootstrap → Router → Dispatcher/Profile Registry → Ollama Execution com transporte falso;
- execução do teste de integração sem TCP, servidor Ollama, GPU ou internet.

O teste oficial de integração utiliza um caso determinístico real da matriz normativa (`RT-017`) e valida que o prompt original do usuário permanece separado do `system_prompt`.

A suíte específica da IMPLEMENTAÇÃO-002.09 foi aprovada com `227 passed in 0.63s`. Sua suíte completa foi aprovada posteriormente com `707 passed in 2.07s`; esse baseline histórico foi substituído pelo gate da IMPLEMENTAÇÃO-002.10, com `893 passed in 2.43s`.

## Matriz normativa

A matriz aprovada está em:

```text
tests/regression/router_v1_cases.json
```

Os testes atuais validam os 48 casos como artefato normativo: IDs, campos, seleção manual, perfil inválido e repetições de determinismo.

O pipeline runtime de normalização, matching, scoring, elegibilidade e decisão está implementado. RT-001–RT-048 são validados tanto como artefato normativo quanto comportamentalmente contra `decide_route()`. RT-045–RT-048 são executados 10 vezes cada para verificar determinismo. Profile Registry, Dispatcher, Runtime Compatibility Validator, configuração operacional oficial, Application Bootstrap e Ollama Execution também estão implementados e validados localmente. RT-017/Unity atravessa hermeticamente o fluxo HTTP → Router → Dispatcher/Profile Registry → Ollama Execution → HTTP, sem rede Ollama real.

## Verificações adicionais

```bash
.venv/bin/python -m compileall -q src tests
git diff --check
```

## CI

O workflow `.github/workflows/tests.yml`:

- usa Python 3.13;
- desabilita persistência de credenciais no checkout;
- aplica timeout;
- compila os módulos;
- instala o pacote com dependências de desenvolvimento;
- executa `python -m pytest -v`.
