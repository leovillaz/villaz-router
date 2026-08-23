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
rules/profiles.yaml
rules/domains.yaml
rules/intents.yaml
rules/routing.yaml
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
- suíte corrente com 333 testes; o checkpoint histórico da `VALIDAÇÃO-001.09` permanece em 228 testes.

## Validação comportamental

RT-001–RT-048 estão executados contra `decide_route()` e reconciliados. Os casos RT-045–RT-048 são repetidos 10 vezes cada para verificar determinismo. O Profile Registry está implementado e validado, e o baseline corrente da suíte é `333 passed`.

## O que ainda não deve ser esperado

Ainda não estão concluídos:

- Dispatcher;
- validação de compatibilidade de runtime entre Router e Profile Registry;
- configuração operacional oficial `profiles/profiles.yaml`;
- integração FastAPI;
- integração Ollama.

Esses itens pertencem às próximas fases.
