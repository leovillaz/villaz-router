# Instalação

## 1. Pré-requisitos

Em Debian/Ubuntu e derivados:

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv
```

Verifique:

```bash
python3 --version
git --version
```

Requisito de Python do projeto:

```text
Python >= 3.13
```

## 2. Clone

```bash
git clone <URL_DO_REPOSITORIO>
cd villaz-router
```

## 3. Ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Verifique:

```bash
python --version
pip --version
```

## 4. Instalação

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## 5. Validação

```bash
pytest -v
```

No estágio documentado deste projeto, a suíte atual contém 66 testes.

## 6. Carregar e validar o ruleset

```bash
python - <<'PY'
from pathlib import Path
from villaz_router.loader import load_and_validate_ruleset_documents

documents = load_and_validate_ruleset_documents(Path("."))

print("semantic validation: OK")
print("profiles:", len(documents.profiles.profiles))
print("domains:", len(documents.domains.domains))
print("intents:", len(documents.intents.intents))
print("routes:", len(documents.routing.routes))
PY
```

Resultado esperado com o ruleset oficial:

```text
semantic validation: OK
profiles: 5
domains: 4
intents: 4
routes: 5
```

## 7. Encerrar o ambiente virtual

```bash
deactivate
```
