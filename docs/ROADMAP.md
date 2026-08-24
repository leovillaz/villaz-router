# Roadmap

## Fase 1 — Bootstrap do Router

- [x] Contratos internos
- [x] Modelos do ruleset
- [x] Loader estrutural
- [x] Validação semântica
- [x] ROUTER-007 — reconciliação normativa e endurecimento de contratos
- [x] RT-001–RT-048 versionados como contrato
- [x] Canonicalização
- [x] JSON determinístico UTF-8
- [x] SHA-256 lógico
- [x] RulesetSnapshot
- [x] Snapshot integrado ao loader

## Fase 2 — Classificação

- [x] Normalização Unicode NFKC
- [x] lowercase/casefold
- [x] collapse whitespace
- [x] accent folding
- [x] boundary matching
- [x] matching de `term`
- [x] matching de `phrase`
- [x] evidência uma vez por request

## Fase 3 — Decisão

- [x] scoring
- [x] threshold
- [x] weak-only gate
- [x] route evaluation
- [x] precedência
- [x] margin
- [x] ambiguous/unrouted
- [x] manual explicit profile
- [x] executar comportamentalmente RT-001–RT-048
- [x] repetir RT-045–RT-048 dez vezes

## Fase 4 — Integrações

Somente após o Router isolado e a matriz comportamental estarem validados:

- [x] Profile Registry
- [x] Dispatcher
- [ ] validação de compatibilidade Router ↔ Profile Registry
- [ ] configuração operacional oficial `profiles/profiles.yaml` após definição de modelos e prompts
- [ ] FastAPI
- [ ] integração com Ollama
- [ ] validar o fluxo API → Router → Dispatcher/Profile Registry → Ollama

## Fase futura

- Orchestrator para workflows multi-perfil;
- Base Fiscal + RAG;
- Villaz Code após o gate do fluxo vertical;
- hot reload versionado, se houver necessidade real;
- observabilidade ampliada.
