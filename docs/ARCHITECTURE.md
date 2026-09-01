# Arquitetura

## Visão geral

O Villaz Router é um núcleo determinístico e isolado.

```text
RouteRequest
    |
    v
Router
    |
    +--> regras declarativas
    +--> normalização
    +--> evidências
    +--> intents/domains
    +--> routes
    |
    v
RouteDecision
```

Integrações externas não pertencem ao core:

```text
HTTP / PromptRequest
        ↓
HTTP Router adapter
        ↓
Router determinístico
        ↓
Dispatcher / Profile Registry
        ↓
OllamaExecutionRequest / OllamaExecutor
        ↓
HTTP / PromptResponse
```

## Entrypoint e configuração de runtime

Os entrypoints `villaz-router serve` e
`python -m villaz_router serve` convergem para a mesma função principal.
A CLI resolve explicitamente uma raiz de configuração e entrega a aplicação
criada por `create_app(configuration_root)` ao Uvicorn.

Sem override, a raiz vem somente dos package resources em
`villaz_router.runtime_data`, resolvidos por `importlib.resources`. O lifetime
do recurso cobre toda a execução do servidor. Com
`--configuration-root PATH`, o caminho externo absoluto substitui
integralmente os recursos empacotados; não há descoberta por cwd, merge ou
fallback.

```text
CLI
  → package resources ou configuration root externo
  → create_app(configuration_root)
  → lifespan: RuntimeContext + OllamaExecutor
  → Uvicorn
```

O bind default é `127.0.0.1:8000`. Host não-loopback exige opção explícita e
gera warning operacional porque a API não possui autenticação como mecanismo
de proteção neste estágio.

## Separação de responsabilidades

### Configuração

`config/router.yaml`

Define parâmetros normativos do engine:

- scoring;
- elegibilidade;
- margem;
- normalização;
- lifecycle;
- integridade;
- privacidade.

### Profiles

`rules/profiles.yaml`

Catálogo de perfis válidos.

### Domains

`rules/domains.yaml`

Classificação técnica baseada em evidências.

No ruleset v1, o domínio `security` representa o assunto técnico de segurança e não seleciona isoladamente o profile `code-review-security`.

A seleção desse profile depende do intent route-capable `review-security`. Evidências que descrevem a ação de revisar, auditar ou procurar vulnerabilidades pertencem ao intent; evidências que descrevem o assunto de segurança pertencem ao domínio.

A associação final a profile continua sendo normativa somente em `routing.yaml`.

### Intents

`rules/intents.yaml`

Classificação de intenção. Apenas intents com `route_capable: true` podem participar de condições de rota.

### Routing

`rules/routing.yaml`

É o único artefato que associa condições semânticas a perfis.

```text
EVIDENCE
   ↓
INTENT / DOMAIN
   ↓
ROUTE
   ↓
PROFILE
```

## Estados finais do Router

- `explicit`
- `routed`
- `ambiguous`
- `unrouted`

Regras:

- `explicit` e `routed` exigem perfil;
- `ambiguous` e `unrouted` exigem `profile = null`;
- não há fallback genérico;
- ambiguidade é resultado legítimo.

## Ollama Execution

A execução com Ollama pertence a uma camada de integração isolada no subpacote `villaz_router.ollama_execution`. Ela não participa da decisão de roteamento e não introduz dependência de Ollama, HTTPX2 ou rede no núcleo determinístico.

A entrada da camada é `OllamaExecutionRequest`, formada por um `DispatchPlan` válido e pelo prompt do usuário mantido separadamente.

As fontes normativas do payload são:

- `DispatchPlan.model` → `model`;
- `DispatchPlan.system_prompt` → `system`;
- `OllamaExecutionRequest.user_prompt` → `prompt`.

A camada não concatena, prefixa ou normaliza `system_prompt` e prompt do usuário.

A única operação Ollama suportada na v1 é `POST /api/generate`, com os campos exatos `model`, `system`, `prompt`, `stream=false`, `raw=false` e `think=false`.

`OllamaExecutor` depende somente do protocolo injetável `OllamaTransport`. A implementação concreta baseada em HTTPX2 permanece interna, permitindo testes com transporte falso sem TCP, Ollama, GPU ou internet.

A construção do executor não realiza rede, preflight, inventário de modelos, preload, download, heartbeat ou polling. A camada também não implementa retry, fallback, persistência automática, shell ou subprocessos.

O endpoint `POST /v1/prompt` executa o fluxo funcional HTTP → adapter → Router → Dispatcher/Profile Registry → OllamaExecutor → HTTP. O `router_adapter.py` conhece somente os contratos HTTP, o `RuntimeContext` e o Router; a composição com Dispatcher e Ollama pertence a `routes.py`.

O fluxo vertical validado de forma hermética é:

    PromptRequest
        ↓
    HTTP Router adapter
        ↓
    decide_route()
        ↓
    RouteDecision
        ↓
    build_dispatch_plan()
        ↓
    DispatchPlan
        ↓
    OllamaExecutionRequest
        ↓
    OllamaExecutor
        ↓
    execute() substituído no boundary Ollama
        ↓
    OllamaExecutionResult
        ↓
    PromptResponse

Esse teste usa a configuração oficial, o Router, o Dispatcher, o Profile Registry e o request de execução reais, mas não realiza conexão de rede.

No lifespan FastAPI, o `RuntimeContext` é inicializado, `config/ollama.yaml` é carregado e um único `OllamaExecutor` é criado, armazenado em `app.state`, reutilizado entre requests e fechado no shutdown. Não há probe Ollama no startup ou na readiness.

O limite bruto de 65.536 bytes é aplicado no ASGI `receive` boundary antes de FastAPI/Pydantic/Router. O composition boundary em `routes.py` também traduz falhas para envelopes públicos seguros, sem expor exceções, `system_prompt`, hashes, configuração ou payload upstream.

## Determinismo

O comportamento deve depender apenas de:

- request;
- configuração;
- ruleset ativo.

Não podem servir como desempate implícito:

- posição física no YAML;
- ordem de detecção;
- ordem alfabética;
- nome de profile;
- filesystem.

## Lifecycle

O ruleset v1 é:

```text
startup_only
```

A instância usa um snapshot imutável durante toda a execução. Alterações em disco só entram em vigor após reinicialização controlada.

## Identidade lógica do ruleset

Após parsing e validação semântica, o control plane é convertido para uma representação lógica canônica.

A identidade inclui:

```text
RouterSettings
+ Profiles
+ Domains
+ Intents
+ Routes
```

A ordem física dos YAMLs não participa da identidade. Profiles, domains, intents, routes e evidências são ordenados deterministicamente por `id`.

O fluxo implementado é:

```text
YAML
  ↓
safe_load
  ↓
modelos Pydantic
  ↓
validação semântica
  ↓
payload canônico
  ↓
JSON determinístico UTF-8
  ↓
SHA-256
  ↓
RulesetSnapshot
```

O `RulesetSnapshot` congela configuração e ruleset para a vida útil da instância.

> **Invariante de decisão:** a ordem canônica por `id` existe exclusivamente para representação, hash e snapshot. Ela não pode ser usada como precedência, desempate ou critério de seleção de rota.
