# Roadmap

## Fase 1 — Bootstrap do Router

- [x] Contratos internos
- [x] Modelos do ruleset
- [x] Loader estrutural
- [x] Validação semântica
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

## Fase 4 — Integrações

Somente após o Router isolado estar validado:

- [ ] Dispatcher / Profile Registry
- [ ] FastAPI
- [ ] Ollama

## Fase futura

- Orchestrator para workflows multi-perfil;
- hot reload versionado, se houver necessidade real;
- observabilidade ampliada.
