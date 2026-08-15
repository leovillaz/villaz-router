# Roadmap

## Fase 1 — Bootstrap do Router

- [x] Contratos internos
- [x] Modelos do ruleset
- [x] Loader estrutural
- [x] Validação semântica
- [x] ROUTER-007 — reconciliação normativa e endurecimento de contratos
- [x] RT-001–RT-048 versionados como contrato
- [ ] Canonicalização
- [ ] SHA-256 lógico
- [ ] RulesetSnapshot

## Fase 2 — Classificação

- [ ] Normalização Unicode NFKC
- [ ] lowercase
- [ ] collapse whitespace
- [ ] accent folding
- [ ] boundary matching
- [ ] matching de `term`
- [ ] matching de `phrase`
- [ ] evidência uma vez por request

## Fase 3 — Decisão

- [ ] scoring
- [ ] threshold
- [ ] weak-only gate
- [ ] route evaluation
- [ ] precedência
- [ ] margin
- [ ] ambiguous/unrouted
- [ ] manual explicit profile
- [ ] executar comportamentalmente RT-001–RT-048
- [ ] repetir RT-045–RT-048 dez vezes

## Fase 4 — Integrações

Somente após o Router isolado e a matriz comportamental estarem validados:

- [ ] Dispatcher / Profile Registry
- [ ] FastAPI
- [ ] integração com Ollama
- [ ] validar o fluxo API → Router → Dispatcher/Profile Registry → Ollama

## Fase futura

- Orchestrator para workflows multi-perfil;
- Base Fiscal + RAG;
- Villaz Code após o gate do fluxo vertical;
- hot reload versionado, se houver necessidade real;
- observabilidade ampliada.
