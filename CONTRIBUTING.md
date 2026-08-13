# Contribuindo

O Villaz Router segue uma abordagem **spec-first e test-first**.

## Regras básicas

1. não alterar comportamento normativo sem teste;
2. não introduzir fallback implícito;
3. não usar ordem física do YAML como regra de desempate;
4. não fazer matching fuzzy no Router v1;
5. manter o Router independente de FastAPI, Ollama e outros componentes de infraestrutura;
6. preservar determinismo;
7. qualquer mudança de ruleset deve passar por validação estrutural e semântica;
8. mudanças de segurança exigem revisão específica.

## Ambiente de desenvolvimento

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## Fluxo recomendado

```bash
git checkout -b feature/minha-alteracao
pytest -v
git diff --check
git add .
git commit -m "feat: describe change"
```

Antes de abrir PR:

```bash
pytest -v
git diff --check
git status
```

## Convenção de commits

Exemplos:

```text
feat: add canonical ruleset hash
fix: reject invalid route reference
test: add regression case for ambiguity
docs: document ruleset lifecycle
refactor: isolate semantic validation
```
