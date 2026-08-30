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
- [x] validação de compatibilidade Router ↔ Profile Registry
- [x] configuração operacional oficial `profiles/profiles.yaml`
- [x] Application Bootstrap com `RuntimeContext` imutável e startup fail-fast
- [x] FastAPI Application Shell, lifecycle e health probes
- [x] camada Ollama Execution assíncrona, injetável e sem acoplamento ao core
- [x] validar Bootstrap → Router → Dispatcher/Profile Registry → Ollama Execution com transporte falso e sem rede
- [ ] implementar endpoint HTTP funcional para prompts
- [ ] validar o fluxo API → Router → Dispatcher/Profile Registry → Ollama

## Publicação pública

Após o fechamento do fluxo vertical funcional:

- [ ] separar configuração pública de configuração operacional privada
- [ ] auditar histórico e working tree para segredos, credenciais e dados pessoais
- [ ] definir política para `system_prompt` operacional e fornecer templates públicos seguros
- [ ] revisar `SECURITY.md`, instalação e guia de replicação
- [ ] escolher licença pública
- [ ] validar reprodução limpa por usuário externo
- [ ] criar tag/release inicial
- [ ] tornar o projeto público

## Fase futura

- Villaz CLI / Villaz Terminal após o gate funcional do Router v1;
- Orchestrator para workflows multi-perfil;
- Base Fiscal + RAG;
- Villaz Code após o gate do fluxo vertical;
- hot reload versionado, se houver necessidade real;
- observabilidade ampliada.
