# Contribuindo

Contribuições ao Villaz Router são recebidas por Pull Request. O projeto segue uma abordagem **spec-first e test-first**.

Não há CLA ou DCO obrigatório neste estágio. Contribuições submetidas intencionalmente e aceitas no projeto ficam sujeitas aos termos aplicáveis da Apache License 2.0.

## Regras básicas

1. manter mudanças pequenas, focadas e revisáveis;
2. não alterar comportamento normativo sem testes adequados;
3. preservar o determinismo;
4. não introduzir fallback implícito;
5. não usar a ordem física do YAML como regra de desempate;
6. não introduzir fuzzy matching no Router v1 sem mudança normativa explícita;
7. manter o núcleo do Router desacoplado das integrações HTTP e Ollama;
8. validar estrutural e semanticamente qualquer mudança de ruleset;
9. submeter mudanças de segurança a revisão específica;
10. nunca incluir segredos, credenciais, caminhos privados ou dados pessoais.

## Ambiente de desenvolvimento

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -v
```

## Fluxo recomendado

Crie uma branch de trabalho e execute as validações relacionadas à mudança. No staging, liste explicitamente somente os arquivos realmente modificados:

```bash
git checkout -b feature/minha-alteracao
pytest -v
git diff --check
git add src/... tests/... docs/...
git commit -m "feat: describe change"
```

Adapte o comando `git add` ao conjunto real de arquivos alterados. Não use o exemplo literalmente para incluir caminhos que não façam parte da contribuição.

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
