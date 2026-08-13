# Testes

## Execução

```bash
pytest -v
```

## Estado atual

A suíte documentada possui **37 testes**.

Cobertura funcional inicial:

- contratos de request/decision;
- invariantes dos estados;
- modelos do ruleset;
- imutabilidade dos modelos;
- leitura dos YAMLs oficiais;
- YAML inválido;
- arquivo ausente;
- documento não-mapping;
- IDs duplicados;
- referências de route inválidas;
- intents não-route-capable;
- versões divergentes;
- evidence inválida;
- ruleset oficial semanticamente válido.

## Verificação adicional

```bash
git diff --check
```

## CI

O repositório inclui workflow GitHub Actions em:

```text
.github/workflows/tests.yml
```

Ele instala o pacote e executa `pytest`.
