# Villaz Router

Router determinístico, declarativo e auditável para seleção de perfis especializados no projeto **Villaz-Lab**.

> **Status:** A IMPLEMENTAÇÃO-002.10 está tecnicamente concluída localmente, incluindo o fluxo funcional HTTP → Router → Dispatcher/Profile Registry → Ollama Execution → HTTP. A suíte completa corrente possui 893 testes aprovados. Próxima etapa: Public Release Hardening e gate de publicação.

## Objetivos

O Villaz Router foi desenhado para:

- selecionar um único perfil especializado de forma determinística;
- usar regras declarativas em YAML;
- separar classificação de intenção/domínio da seleção de perfil;
- manter decisões reproduzíveis e auditáveis;
- rejeitar rulesets estrutural ou semanticamente inválidos;
- não depender de LLM para decidir o roteamento;
- preservar segurança e privacidade como requisitos transversais.

## Estado atual

Implementado e testado:

- contratos `RouteRequest`, `RouteDecision` e erros internos;
- coerência entre estado, modo, razão, candidatos e conflito;
- modelos formais de configuração e ruleset;
- loader seguro de YAML;
- validação estrutural com Pydantic;
- validação semântica e de referências cruzadas;
- validação de IDs, versões, scoring e profiles desabilitados;
- ruleset oficial v1;
- separação normativa Domain × Intent para Security / Code Review;
- rota `code-review-security` condicionada ao intent `review-security`;
- matriz normativa RT-001–RT-048 em `tests/regression`;
- canonicalização semântica independente da ordem física do YAML;
- JSON determinístico UTF-8;
- hash lógico SHA-256;
- `RulesetSnapshot` imutável integrado ao loader;
- normalização determinística com NFKC, `casefold()`, remoção de diacríticos e colapso de whitespace;
- matching simétrico de evidências `term` e `phrase`;
- fronteiras formais de `term` com letras Unicode, números e `_` como caracteres de palavra;
- `EvidenceMatch` imutável com posição da primeira ocorrência válida;
- matching agregado determinístico ordenado por `evidence_id`;
- `match_evidence` e `match_evidence_set` recebem a mensagem já normalizada em `normalized_message`; `evidence.value` é normalizado internamente pelo matcher;
- validação fail-fast de evidência que normalize para vazio;
- scoring determinístico baseado em `EvidenceStrength` e `ScoringConfig`;
- resultado estruturado por `EvidenceContribution` e `ScoringResult`;
- validações fail-fast de integridade entre `EvidenceMatch` e `Evidence`;
- API pública `score_evidence_matches`;
- elegibilidade por `minimum_score` e weak-only gate;
- avaliação determinística de Domains e Intents;
- qualificação estrutural de Routes;
- gate de conflito entre múltiplos Intents `route_capable`;
- precedência por maior `priority`;
- resolução por `comparison_score` e `minimum_margin`;
- estados finais `explicit`, `routed`, `ambiguous` e `unrouted`;
- candidatos ambíguos canônicos por score decrescente e `route_id` crescente;
- `RouteCandidate` e `RouteDecision` com invariantes de estado;
- API pública `decide_route`;
- Profile Registry com `ProfileDefinition`, `ProfileRegistrySnapshot`, erros próprios, loader YAML, canonicalização e `registry_hash` determinístico;
- APIs públicas do Registry exportadas pelo pacote `villaz_router`;
- configuração operacional oficial materializada em `profiles/profiles.yaml`, com cinco profiles habilitados, modelos base executáveis e `system_prompt` canônico no Registry;
- catálogo operacional validado em compatibilidade 1:1 com o catálogo do Router;
- Dispatcher determinístico com domínio próprio de erros, `DispatchPlan` imutável e API pública `build_dispatch_plan`;
- tradução controlada de erros do Registry, rejeição de estados não despacháveis e ausência de fallback;
- direção arquitetural protegida: Router + Registry → Dispatcher;
- Runtime Compatibility Validator puro e determinístico entre `RulesetSnapshot` e `ProfileRegistrySnapshot`;
- validação fail-fast de referência de Route, catálogo 1:1 Router ↔ Registry e estado `enabled`;
- domínio próprio de erros com `RuntimeCompatibilityError`, `RuntimeCompatibilityErrorCode` e `RuntimeCompatibilityReason`;
- API pública `validate_runtime_compatibility()` exportada pelo pacote `villaz_router`;
- Runtime Compatibility Validator sem dependência de Dispatcher, loaders, canonicalização, FastAPI, Ollama, filesystem ou rede;
- Application Bootstrap síncrono com API pública `bootstrap_runtime(configuration_root)`;
- validação explícita e fail-fast da raiz de configuração;
- carregamento sequencial Ruleset → Profile Registry → Runtime Compatibility;
- `RuntimeContext` imutável contendo a raiz normalizada e exatamente os snapshots validados;
- domínio próprio `ApplicationBootstrapError`, com estágio, código, mensagem e causa preservada;
- ausência de estado global, fallback, retry, I/O de importação ou captura genérica de erros inesperados;
- separação arquitetural preservada: a camada FastAPI depende do bootstrap, enquanto o bootstrap permanece independente de FastAPI, HTTP e Ollama;
- APIs públicas `bootstrap_runtime`, `RuntimeContext`, `BootstrapStage`, `ApplicationBootstrapErrorCode` e `ApplicationBootstrapError`;
- aplicação FastAPI isolada em `villaz_router.http_api`;
- factory pública `create_app(configuration_root)`, sem singleton global, bootstrap ou I/O durante sua criação;
- lifespan moderno executando `bootstrap_runtime()` exatamente uma vez por ciclo e antes de servir requisições;
- configuração oficial do Ollama em `config/ollama.yaml`, carregada no lifespan por `config_loader.py`;
- um único `OllamaExecutor` criado no startup, reutilizado entre requests e fechado no shutdown, sem probe de rede;
- `RuntimeContext` e `OllamaExecutor` publicados em `app.state` e removidos no encerramento;
- dependencies públicas e tipadas `get_runtime_context(request)` e `get_ollama_executor(request)`;
- `GET /health/live` como liveness simples e `GET /health/ready` condicionado à validade do contexto e do executor, sem probe Ollama;
- limite global no ASGI `receive` boundary, antes de FastAPI/Pydantic/Router: 65.536 bytes permitidos e 65.537 bytes rejeitados com HTTP 413 e `REQUEST_TOO_LARGE`;
- `router_adapter.py` como fronteira HTTP do Router, sem dependência de Dispatcher, Ollama ou responses FastAPI;
- endpoint funcional `POST /v1/prompt`, compondo Router, Dispatcher/Profile Registry e Ollama Execution;
- mapeamento seguro de erros HTTP, sem exposição de exceções, prompts internos, hashes, configuração ou payload upstream:
  - estado `AMBIGUOUS` → HTTP 409;
  - `UNROUTED` → HTTP 422;
  - `INVALID_PROFILE` → HTTP 422;
  - `INTERNAL_ERROR` → HTTP 500;
  - `MODEL_SERVICE_TIMEOUT` → HTTP 504;
  - `MODEL_SERVICE_UNAVAILABLE` → HTTP 503;
  - `MODEL_SERVICE_ERROR` → HTTP 502;
  - `HTTP_STATUS_ERROR` do Ollama é traduzido para `MODEL_SERVICE_ERROR` → HTTP 502, sem propagar o status upstream;
- cancelamento assíncrono preservado sem conversão em erro HTTP;
- integração vertical hermética do caso normativo RT-017/Unity até o boundary Ollama;
- OpenAPI, Swagger UI e ReDoc explicitamente desabilitados;
- proteção arquitetural entre núcleo, Application Bootstrap e adaptador HTTP;
- FastAPI `0.141.1` e HTTPX2 `2.12.0` com versões fixadas;
- suíte corrente com 893 testes, sem failures, skips, xfails, warnings do pytest ou erros de collection.

Próxima etapa planejada:

- executar o Public Release Hardening;
- concluir o gate Git e de publicação, ainda pendente.

Consulte [docs/ROUTER_007.md](docs/ROUTER_007.md).

## Requisitos

- Linux
- Python 3.13+
- Git
- `python3-venv`
- `pip`

Ambiente usado durante o desenvolvimento inicial:

- Python 3.13.5
- Git 2.47.3

## Instalação rápida

```bash
git clone <URL_DO_REPOSITORIO>
cd villaz-router

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev]"

pytest -v
```

Consulte [docs/INSTALLATION.md](docs/INSTALLATION.md) para o procedimento completo.

## Estrutura

```text
villaz-router/
├── config/
│   ├── ollama.yaml
│   └── router.yaml
├── rules/
│   ├── profiles.yaml
│   ├── domains.yaml
│   ├── intents.yaml
│   └── routing.yaml
├── profiles/
│   └── profiles.yaml
├── src/
│   └── villaz_router/
├── tests/
│   ├── unit/
│   └── regression/
├── docs/
├── .github/
│   └── workflows/
├── pyproject.toml
└── README.md
```

## Pipeline do ruleset

```text
YAML
  ↓
safe_load
  ↓
validação estrutural
  ↓
validação semântica
  ↓
canonicalização semântica
  ↓
JSON determinístico UTF-8
  ↓
SHA-256 lógico
  ↓
RulesetSnapshot imutável
  ↓
Router
```

## Perfis oficiais v1

| Profile | Modelo base | Enabled |
| --- | --- | :---: |
| `code-review-security` | `qwen2.5-coder:14b` | `true` |
| `docs-dev` | `gemma3:12b` | `true` |
| `fiscal-finance` | `qwen3:14b` | `true` |
| `mobile-dev` | `qwen2.5-coder:14b` | `true` |
| `unity-dev` | `qwen2.5-coder:14b` | `true` |

A configuração operacional canônica está em `profiles/profiles.yaml`. O campo `system_prompt` do Profile Registry é a fonte normativa das instruções comportamentais de cada profile; aliases especializados existentes no Ollama não constituem uma segunda fonte de verdade.

## Precedência das rotas v1

| Prioridade | Rota | Perfil |
|---:|---|---|
| 500 | review-security | `code-review-security` |
| 450 | fiscal | `fiscal-finance` |
| 400 | documentation | `docs-dev` |
| 300 | unity | `unity-dev` |
| 200 | mobile | `mobile-dev` |

A seleção manual de perfil tem precedência sobre o roteamento automático.

## Documentação

- [Instalação](docs/INSTALLATION.md)
- [Guia de replicação](docs/REPLICATION_GUIDE.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Configuração](docs/CONFIGURATION.md)
- [Referência do ruleset](docs/RULESET_REFERENCE.md)
- [Desenvolvimento](docs/DEVELOPMENT.md)
- [Testes](docs/TESTING.md)
- [Status do projeto](docs/PROJECT_STATUS.md)
- [Roadmap](docs/ROADMAP.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Segurança](SECURITY.md)
- [Contribuição](CONTRIBUTING.md)

## Segurança e privacidade

O Router não deve registrar automaticamente a mensagem integral do usuário. O ruleset oficial v1 usa:

```yaml
privacy:
  store_full_message: false
  store_evidence: true
```

Veja [SECURITY.md](SECURITY.md).

## Licença

A licença pública ainda deve ser escolhida antes da abertura do repositório. Enquanto o repositório permanecer privado, não há licença pública concedida por este projeto.
