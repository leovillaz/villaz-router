# Testes

## Execução

```bash
python -m pytest -v
```

## Estado atual

A suíte documentada possui **66 testes**.

Cobertura atual:

- contratos de request/decision;
- coerência entre estado, modo, razão, candidatos e conflito;
- modelos e imutabilidade do ruleset;
- leitura segura dos YAMLs oficiais;
- YAML inválido, arquivo ausente e documento não-mapping;
- IDs, versões e evidências inválidas;
- referências cruzadas;
- profiles desabilitados;
- prioridades duplicadas aceitas como precedência válida;
- coerência de scoring e threshold agregado;
- `minimum_score` superior a uma evidência `strong` aceito;
- normalização accent-insensitive na validação de duplicatas;
- associação da rota de segurança ao intent `review-security`;
- integridade do contrato RT-001–RT-048;
- canonicalização determinística do ruleset;
- independência da ordem física de profiles, domains, intents, routes e evidências;
- serialização compacta em JSON UTF-8;
- mudanças semânticas alterando o hash;
- reordenação física preservando o hash;
- formato SHA-256 hexadecimal minúsculo;
- criação e estabilidade do `RulesetSnapshot`;
- inclusão das configurações do Router no snapshot;
- integração do snapshot ao loader.

## Matriz normativa

A matriz aprovada está em:

```text
tests/regression/router_v1_cases.json
```

Os testes atuais validam os 48 casos como artefato normativo: IDs, campos, seleção manual, perfil inválido e repetições de determinismo.

A execução das mensagens pelo Router ainda está pendente. Ela só será habilitada após normalização, matching, scoring e algoritmo de decisão serem implementados.

## Verificações adicionais

```bash
python -m compileall -q src tests
git diff --check
```

## CI

O workflow `.github/workflows/tests.yml`:

- usa Python 3.13;
- desabilita persistência de credenciais no checkout;
- aplica timeout;
- compila os módulos;
- instala o pacote com dependências de desenvolvimento;
- executa `python -m pytest -v`.
