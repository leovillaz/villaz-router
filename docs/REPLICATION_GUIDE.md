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
python - <<'PY'
from pathlib import Path
from villaz_router.loader import load_and_validate_ruleset_documents

load_and_validate_ruleset_documents(Path("."))
print("ruleset: OK")
PY
```

## Resultado mínimo para considerar a réplica válida

- dependências instaladas;
- pacote `villaz_router` importável;
- testes aprovados;
- ruleset carregado;
- validação semântica aprovada;
- working tree Git limpo.

## O que ainda não deve ser esperado

No estado atual, ainda não estão concluídos:

- canonicalização;
- hash lógico;
- snapshot final;
- normalização de mensagem;
- matching;
- scoring;
- seleção automática final;
- integração FastAPI;
- integração Ollama.

Esses itens pertencem às próximas fases.
