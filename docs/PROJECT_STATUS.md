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

## Validação atual

```text
37 passed
```

Ruleset oficial:

```text
profiles: 5
domains: 4
intents: 4
routes: 5
```

## Próxima etapa

### IMPLEMENTAÇÃO-001.05

- canonicalização semântica;
- JSON determinístico UTF-8;
- SHA-256 lógico;
- criação de `RulesetSnapshot`.

## Ainda não implementado

- matching;
- scoring em runtime;
- algoritmo de decisão;
- FastAPI;
- Dispatcher;
- Profile Registry;
- Ollama;
- Orchestrator.
