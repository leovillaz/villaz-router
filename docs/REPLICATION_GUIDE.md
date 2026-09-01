# Guia de replicação

Este documento descreve como reproduzir o estado funcional atual do Villaz Router em outra máquina.

## Etapa A — Preparar a máquina

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv
```

## Etapa B — Obter o código

```bash
git clone <URL_DO_REPOSITORIO>
cd villaz-router
```

## Etapa C — Criar ambiente isolado

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Etapa D — Conferir os artefatos normativos

Devem existir:

```text
config/router.yaml
config/ollama.yaml
profiles/profiles.yaml
rules/profiles.yaml
rules/domains.yaml
rules/intents.yaml
rules/routing.yaml
```

No startup, `create_app()` inicializa o `RuntimeContext`, carrega `config/ollama.yaml` e cria um único `OllamaExecutor` no lifespan. O contexto e o executor são reutilizados entre requests e removidos após o fechamento do executor no shutdown. Esse processo não realiza probe de rede Ollama.

O endpoint funcional é `POST /v1/prompt`. Seu fluxo é:

```text
HTTP → PromptRequest → HTTP Router adapter → Router → Dispatcher/Profile Registry → OllamaExecutionRequest → OllamaExecutor → HTTP PromptResponse
```

## Etapa E — Executar os testes

```bash
pytest -v
```

## Etapa F — Validar o ruleset

```bash
python -c 'from pathlib import Path; from villaz_router.loader import load_and_validate_ruleset_documents; load_and_validate_ruleset_documents(Path(".")); print("ruleset: OK")'
```

## Resultado mínimo para considerar a réplica válida

- dependências instaladas;
- pacote `villaz_router` importável;
- testes aprovados;
- ruleset carregado;
- validação semântica aprovada;
- working tree Git limpo.

## O que já está concluído

No estado atual, já estão concluídos:

- canonicalização semântica;
- JSON determinístico UTF-8;
- hash lógico SHA-256;
- `RulesetSnapshot`;
- normalização determinística de mensagem;
- matching de `term` e `phrase`;
- validação de evidências normalizadas;
- scoring determinístico em runtime;
- `EvidenceContribution` e `ScoringResult`;
- validações de integridade entre matches e evidências configuradas;
- elegibilidade por threshold e weak-only gate;
- qualificação estrutural de Routes;
- resolução por prioridade e margem;
- gate de conflito entre Intents `route_capable`;
- `RouteCandidate` e `RouteDecision`;
- API pública `decide_route`;
- Profile Registry determinístico;
- Dispatcher com `DispatchPlan` e API pública `build_dispatch_plan`;
- Runtime Compatibility Validator entre Ruleset e Profile Registry;
- configuração operacional oficial com cinco profiles habilitados;
- Application Bootstrap com `bootstrap_runtime()` e `RuntimeContext` imutável;
- aplicação FastAPI funcional com `create_app()`, lifecycle fail-fast, health probes e `POST /v1/prompt`;
- Ollama Execution assíncrona e injetável em `villaz_router.ollama_execution`;
- configuração oficial `config/ollama.yaml` carregada por `config_loader.py`;
- configuração explícita por `OllamaClientConfig`, `OllamaTimeoutConfig` e `OllamaConnectionLimits`;
- `OllamaExecutor` com transporte abstrato `OllamaTransport`;
- implementação HTTPX2 interna para `POST /api/generate`;
- integração oficial Bootstrap → Router → Dispatcher/Profile Registry → Ollama Execution validada com transporte falso e sem rede;
- integração vertical HTTP de RT-017/Unity validada substituindo somente o boundary Ollama;
- suíte corrente com 893 testes; os checkpoints históricos da `VALIDAÇÃO-001.09`, do Dispatcher, do Application Bootstrap e da Ollama Execution permanecem, respectivamente, em 228, 384, 435 e 707 testes.

## Validação comportamental

RT-001–RT-048 estão executados contra `decide_route()` e reconciliados. Os casos RT-045–RT-048 são repetidos 10 vezes cada para verificar determinismo. Profile Registry, Dispatcher, Runtime Compatibility Validator, configuração operacional oficial, Application Bootstrap, aplicação FastAPI e Ollama Execution estão implementados e validados. RT-017 também percorre o fluxo vertical via `POST /v1/prompt`, usando Router, Dispatcher, Registry e `OllamaExecutionRequest` reais; somente a execução final é simulada no boundary Ollama. Os testes automatizados não exigem TCP, servidor Ollama, GPU ou internet. O baseline corrente da suíte completa é `893 passed in 2.43s`.

## O que ainda não deve ser esperado

Ainda não estão concluídos:

- autenticação e autorização;
- servidor ASGI e deployment;
- Public Release Hardening e gate de publicação.

Esses itens pertencem às próximas fases; a IMPLEMENTAÇÃO-002.10 está tecnicamente concluída localmente, mas ainda não foi publicada.
