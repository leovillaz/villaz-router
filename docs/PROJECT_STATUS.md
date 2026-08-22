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
228 passed
```

A suíte atual comprova modelos, loader, validação semântica, invariantes, integridade da matriz, canonicalização, identidade SHA-256, criação determinística do `RulesetSnapshot`, normalização, matching, scoring, elegibilidade, qualificação estrutural de Routes e decisão determinística em runtime.

A execução comportamental integral dos 48 casos RT permanece como próxima etapa.

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

## IMPLEMENTAÇÃO-001.07 — concluída

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
- API pública `score_evidence_matches`.

Suíte vigente ao fechamento técnico:

```text
124 passed
```

## IMPLEMENTAÇÃO-001.08 — concluída tecnicamente

Implementado:

- modelo público e imutável `RouteCandidate`;
- evolução de `RouteDecision` com `route_id` e `comparison_score`;
- elegibilidade por `minimum_score`;
- weak-only gate em runtime;
- avaliação determinística de Domains e Intents;
- qualificação estrutural de Routes;
- `comparison_score` transitório sem soma Domain + Intent;
- gate de conflito entre múltiplos Intents `route_capable`;
- precedência por maior `priority`;
- resolução por `minimum_margin`;
- empate no topo tratado como ambiguidade;
- candidatos ambíguos ordenados por `comparison_score` DESC e `route_id` ASC;
- precedência absoluta de `explicit_profile`;
- perfil explícito inválido ou desabilitado retornando `INVALID_PROFILE`, sem fallback;
- mapeamento determinístico de `RoutingReason`;
- semântica de `conflict_resolved`;
- estados finais `explicit`, `routed`, `ambiguous` e `unrouted`;
- API pública `decide_route`.

Suíte vigente ao fechamento técnico:

```text
180 passed
```

## VALIDAÇÃO-001.09 — concluída tecnicamente

Validado:

- executor comportamental de RT-001–RT-048 contra `decide_route()`;
- 48 casos executados com sucesso;
- RT-045–RT-048 executados 10 vezes cada conforme contrato de determinismo;
- `RT-015` e `RT-032` reconciliados em `conflict_resolved=false`, preservando mensagem, perfil, reason e ruleset;
- divergências classificadas como inconsistência da matriz normativa, não erro de implementação ou ruleset;
- suíte completa ao fechamento técnico: `228 passed`;
- `git diff --check` aprovado.

## Próxima etapa

- Dispatcher / Profile Registry.

## Ainda não implementado

- Dispatcher;
- Profile Registry;
- FastAPI;
- Ollama;
- Orchestrator.
