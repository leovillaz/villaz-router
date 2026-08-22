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
124 passed
```

A suíte atual comprova modelos, loader, validação semântica, invariantes, integridade da matriz, canonicalização, identidade SHA-256, criação determinística do `RulesetSnapshot`, normalização, matching determinístico e scoring runtime com validações de integridade. A execução comportamental dos 48 casos depende agora da implementação da camada de elegibilidade e decisão.

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

## IMPLEMENTAÇÃO-001.06 — concluída tecnicamente

Implementado:

- normalização determinística com NFKC, `casefold()`, remoção de diacríticos e colapso de whitespace;
- preservação de pontuação;
- `EvidenceMatch` Pydantic congelado e estrito;
- matching de `phrase` por substring literal contínua;
- matching de `term` com fronteiras formais Unicode/número/`_`;
- primeira ocorrência válida por evidência;
- matching agregado imutável ordenado por `evidence_id`;
- normalização simétrica de mensagem e `evidence.value`;
- rejeição semântica fail-fast de evidência que normalize para vazio;
- APIs públicas `normalize_text`, `match_evidence`, `match_evidence_set` e `EvidenceMatch`.

Suíte vigente ao fechamento técnico:

```text
97 passed
```

## IMPLEMENTAÇÃO-001.07 — em fechamento técnico

Implementado:

- modelos públicos `EvidenceContribution` e `ScoringResult`;
- invariant estrutural `score == soma dos weights`;
- código `INVALID_SCORING_INPUT`;
- scoring configurável por `ScoringConfig`;
- associação determinística `EvidenceMatch` → `Evidence` por `evidence_id`;
- validação de IDs duplicados, referências desconhecidas e divergências de tipo/valor;
- ordem fail-fast determinística;
- contribuições canonicalizadas por `evidence_id`;
- suporte a iteráveis e generators;
- API `score_evidence_matches`.

Suíte atual:

```text
124 passed
```

## Próxima etapa

- elegibilidade e algoritmo determinístico de decisão.

## Ainda não implementado

- threshold/eligibilidade em runtime;
- weak-only gate em runtime;
- algoritmo de decisão;
- execução comportamental de RT-001–RT-048;
- FastAPI;
- Dispatcher;
- Profile Registry;
- Ollama;
- Orchestrator.
