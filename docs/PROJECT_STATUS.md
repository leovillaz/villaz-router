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
435 passed
```

A suíte corrente comprova Router, execução comportamental integral de RT-001–RT-048, Profile Registry, Dispatcher, Runtime Compatibility Validator, configuração operacional oficial e Application Bootstrap determinístico. Os checkpoints históricos mantêm seus respectivos totais de testes nas seções abaixo.



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

Suíte vigente naquele checkpoint:

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

## IMPLEMENTAÇÃO-002.02 — Profile Registry — concluída tecnicamente

Implementado e validado:

- domínio de erros próprio com `RegistryErrorCode` e `RegistryError`;
- `ProfileDefinition` imutável com IDs canônicos e strings obrigatórias sem normalização destrutiva;
- `ProfileRegistrySnapshot` imutável, ordenado e com `profile_ids` derivados;
- resolução exata por `get()`, `contains()` e `list_profiles()`;
- canonicalização lógica independente da ordem física do YAML;
- `registry_hash` SHA-256 determinístico conforme contrato aprovado;
- loader próprio de `profiles/profiles.yaml`, sem reutilizar helpers privados do Router;
- tradução de falhas em `INVALID_REGISTRY`, `INVALID_PROFILE_DEFINITION` e `DUPLICATE_PROFILE_ID`;
- cobertura integrada loader → definição → canonicalização → snapshot;
- exports públicos do Profile Registry pelo pacote `villaz_router`;
- suíte completa no fechamento técnico: `333 passed`;
- `git diff --check` aprovado.

Observação histórica deste checkpoint: o arquivo operacional oficial `profiles/profiles.yaml` ainda não havia sido criado. Essa pendência foi resolvida posteriormente na IMPLEMENTAÇÃO-002.06.

## IMPLEMENTAÇÃO-002.04 — Dispatcher — concluída e publicada

Implementado e validado:

- domínio próprio `DispatcherErrorCode` / `DispatcherError`;
- modelo imutável `DispatchPlan` com validação de estado, `route_id`, hash e campos obrigatórios;
- API pura `build_dispatch_plan(decision, registry)`;
- suporte somente aos estados `routed` e `explicit`;
- rejeição imediata de `ambiguous` e `unrouted`, sem consulta ao Registry;
- resolução exata do perfil pelo Profile Registry;
- tradução exclusiva de `RegistryErrorCode.PROFILE_NOT_FOUND` para o domínio do Dispatcher, preservando `__cause__`;
- perfil desabilitado tratado como erro, sem fallback;
- `ValidationError` do `DispatchPlan` convertido somente na fronteira final para `INVALID_DISPATCH_PLAN`;
- exceções inesperadas e erros não relacionados do Registry não são mascarados;
- exports públicos `build_dispatch_plan`, `DispatchPlan`, `DispatcherError` e `DispatcherErrorCode`;
- direção de dependências protegida: Router + Registry → Dispatcher;
- testes específicos do Dispatcher: `51 passed`;
- suíte completa no fechamento técnico: `384 passed`;
- `git diff --check` aprovado.

O Dispatcher foi publicado no commit `0d86e74f696519e8944a8129e3ab83be47409e67`.

## IMPLEMENTAÇÃO-002.05 — Runtime Compatibility Validator — concluída e publicada

Implementado e validado:

- API pura `validate_runtime_compatibility(ruleset, registry)`;
- validação determinística de referências de Routes;
- compatibilidade 1:1 entre os catálogos do Router e do Registry;
- validação do estado `enabled`;
- domínio independente `RuntimeCompatibilityError`;
- razões estruturadas e ordem fail-fast determinística;
- nenhuma dependência de Dispatcher, loaders, filesystem, FastAPI, Ollama ou rede;
- suíte completa ao fechamento: `411 passed`;
- commit publicado: `9ce02487ab7adaee6bb4de70755da04d66af23a7`.

## IMPLEMENTAÇÃO-002.06 — Configuração operacional dos Profiles — concluída e publicada

Implementado e validado:

- `profiles/profiles.yaml` oficial;
- cinco profiles operacionais, todos habilitados;
- `ProfileDefinition.system_prompt` como fonte normativa do comportamento;
- modelos base executáveis registrados em `ProfileDefinition.model`;
- aliases especializados do Ollama sem autoridade normativa;
- catálogo Router ↔ Registry validado em compatibilidade 1:1;
- `registry_hash` oficial: `c9b7ef321815b11f6a38fcd0c4b3538bc549e78a41a1149760e3c49f8dcbf6af`;
- teste integrado da configuração operacional oficial;
- suíte completa ao fechamento: `412 passed`;
- commit publicado: `cc87f0b79380f77c3dafd8804b5e547e9580538a`.

## IMPLEMENTAÇÃO-002.07 — Application Bootstrap — concluída tecnicamente

Implementado e validado:

- API pública síncrona `bootstrap_runtime(configuration_root)`;
- raiz explícita, obrigatória, absoluta e validada;
- sequência determinística Ruleset → Profile Registry → Runtime Compatibility → `RuntimeContext`;
- `RuntimeContext` imutável com exatamente a raiz e os snapshots aprovados;
- domínio próprio `ApplicationBootstrapError`;
- estágios e códigos estruturados, com causa original preservada;
- interrupção na primeira falha, sem retry, fallback ou estado parcial;
- erros inesperados não são mascarados;
- ausência de estado global e de I/O durante importação;
- independência de FastAPI, HTTP, ASGI, Ollama e rede;
- exports públicos do bootstrap;
- teste integrado com a configuração operacional oficial;
- 23 novos testes;
- suíte completa corrente: `435 passed`;
- `git diff --check` aprovado.

## Próxima etapa

- integrar FastAPI e seu lifecycle ao `RuntimeContext`;
- integrar a execução dos modelos com Ollama a partir do `DispatchPlan`;
- validar o fluxo vertical API → Router → Dispatcher/Profile Registry → Ollama.

## Ainda não implementado

- FastAPI;
- integração Ollama;
- fluxo vertical completo;
- Orchestrator.
