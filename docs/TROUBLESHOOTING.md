# Troubleshooting

## `pip3: comando não encontrado`

Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv
```

## Import do pacote falha

Ative o venv e instale editável:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

## Ruleset não encontrado

Confirme:

```bash
find config rules -maxdepth 2 -type f -print | sort
```

Devem existir:

```text
config/router.yaml
rules/domains.yaml
rules/intents.yaml
rules/profiles.yaml
rules/routing.yaml
```

## `INVALID_RULESET`

Execute os testes:

```bash
pytest -v
```

Depois valide diretamente:

```bash
python - <<'PY'
from pathlib import Path
from villaz_router.loader import load_and_validate_ruleset_documents

load_and_validate_ruleset_documents(Path("."))
print("OK")
PY
```

## Git não reconhece o diretório

```bash
git init
git branch -M main
```

## Working tree inesperadamente sujo

```bash
git status
git diff
git diff --check
```
