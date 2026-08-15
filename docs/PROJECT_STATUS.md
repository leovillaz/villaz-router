# Status do projeto

## Implementação concluída

### IMPLEMENTAÇÃO-001.01
Contratos internos e invariantes básicas.

### IMPLEMENTAÇÃO-001.02
Modelos formais do ruleset.

### IMPLEMENTAÇÃO-001.03
Loader estrutural dos YAMLs.

### IMPLEMENTAÇÃO-001.04
Validação semântica e referências cruzadas.

### ROUTER-007
Reconciliação entre a especificação consolidada e o repositório:

- separação Domain × Intent preservada em Security / Code Review;
- rota `code-review-security` condicionada ao intent `review-security`;
- evidências aprovadas sincronizadas com o ruleset;
- invariantes de `RouteDecision` fortalecidas;
- validação de IDs, versões, scoring e profiles desabilitados;
- prioridades duplicadas permitidas como precedência válida;
- `minimum_score` permitido acima de uma evidência `strong`;
- matriz RT-001–RT-048 versionada como contrato de regressão.

## Validação atual

```text
66 passed
```

A suíte atual comprova modelos, loader, validação semântica, invariantes, integridade da matriz, canonicalização, identidade SHA-256 e criação determinística do `RulesetSnapshot`. A execução comportamental dos 48 casos depende da implementação futura de normalização, matching, scoring e decisão.

Ruleset oficial:

```text
profiles: 5
domains: 4
intents: 4
routes: 5
regression cases: 48
```

## IMPLEMENTAÇÃO-001.05 — concluída

Implementado:

- canonicalização semântica;
- JSON determinístico UTF-8;
- SHA-256 lógico;
- `RulesetSnapshot`;
- inclusão de `RouterSettings` no snapshot;
- integração do snapshot ao loader;
- independência da ordem física das coleções YAML;
- validação de formato hexadecimal SHA-256.

Hash lógico do ruleset oficial `1.0.0` neste checkpoint:

```text
ee57b50c8ff5f15476276610b6850c30509933e129a7a43062159348e0cbe575
```

Suíte atual:

```text
66 passed
```

## Próxima etapa

- normalização de mensagens;
- matching determinístico.

## Ainda não implementado

- normalização de mensagens;
- matching;
- scoring em runtime;
- algoritmo de decisão;
- execução comportamental de RT-001–RT-048;
- FastAPI;
- Dispatcher;
- Profile Registry;
- Ollama;
- Orchestrator.
