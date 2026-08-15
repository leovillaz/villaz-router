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
52 passed
```

A suíte atual comprova modelos, loader, validação semântica, invariantes e integridade da matriz. A execução comportamental dos 48 casos depende da implementação futura de normalização, matching, scoring e decisão.

Ruleset oficial:

```text
profiles: 5
domains: 4
intents: 4
routes: 5
regression cases: 48
```

## Próxima etapa

### IMPLEMENTAÇÃO-001.05

- canonicalização semântica;
- JSON determinístico UTF-8;
- SHA-256 lógico;
- criação de `RulesetSnapshot`.

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
