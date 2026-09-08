# Roadmap

## Router v1

- [x] contratos e modelos formais;
- [x] loader e validação estrutural/semântica;
- [x] normalização, matching, scoring e elegibilidade;
- [x] estados `explicit`, `routed`, `ambiguous` e `unrouted`;
- [x] matriz normativa RT-001–RT-048;
- [x] canonicalização, snapshot e hash lógico;
- [x] decisão determinística sem LLM.

## Runtime e integrações

- [x] Profile Registry;
- [x] Dispatcher;
- [x] compatibilidade Router ↔ Registry;
- [x] configuração operacional oficial;
- [x] Application Bootstrap fail-fast;
- [x] Ollama Execution assíncrona e injetável;
- [x] API FastAPI, lifecycle e health endpoints;
- [x] `POST /v1/prompt`;
- [x] fluxo HTTP → Router → Dispatcher/Profile Registry → Ollama → HTTP;
- [x] integração vertical hermética RT-017/Unity.

## Public Release Hardening

- [x] Apache License 2.0 e metadados públicos;
- [x] CLI pública e package resources;
- [x] documentação pública base reconciliada;
- [x] hardening de CI e supply chain implementado;
- [x] commit e push do hardening publicados na `main`;
- [x] repositório aberto ao público;
- [x] clean install em ambiente third-party;
- [x] verificação dos artefatos usados no clean install por SHA-256;
- [x] E2E operacional com Ollama e modelo real;
- [x] deployment Linux com `systemd` e restart-on-failure validado;
- [x] exposição LAN-only controlada por `nftables` validada;
- [x] reboot acceptance no host de referência;
- [x] reboot acceptance na VM third-party com health e inferência remota pós-boot;
- [ ] reconciliar e confirmar CI remoto no estado publicado;
- [ ] GitHub Private Vulnerability Reporting habilitado e validado;
- [ ] publication gate final;
- [ ] tag e release inicial.

## Evoluções posteriores ao v1

Somente após o publication gate:

- Orchestrator para workflows multi-profile;
- Villaz Terminal e expansão da experiência de CLI;
- Base Fiscal + RAG;
- Villaz Code;
- hot reload versionado, se houver necessidade normativa;
- observabilidade ampliada sem exposição de dados sensíveis.
