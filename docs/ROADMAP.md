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
- [x] documentação pública reconciliada;
- [x] hardening de CI e supply chain, incluindo execução remota bem-sucedida no GitHub;
- [x] commit e push do hardening publicados na `main`;
- [x] clean clone e clean install do Public Release Hardening;
- [x] validação de wheel/sdist do Public Release Hardening;
- [x] GitHub Private Vulnerability Reporting habilitado e validado;
- [x] E2E operacional com Ollama e modelos reais;
- [x] publication gate;
- [x] abertura pública do repositório;
- [ ] tag e GitHub Release inicial.

## Operational Deployment & Portability

- [x] Linux reference deployment;
- [x] systemd e identidade operacional;
- [x] autostart, restart e stop semantics;
- [x] bind LAN e firewall;
- [x] health e diagnóstico;
- [x] reboot acceptance e inferência real pós-reboot;
- [x] third-party clean install em Debian 13;
- [x] third-party deployment com systemd e nftables;
- [x] reboot acceptance third-party com health e inferência remota pós-boot;
- [ ] publicação dos artefatos da release inicial;
- [ ] Windows nativo e WSL2;
- [ ] Docker/Compose;
- [ ] documentação e gate final de deployment/portabilidade.

## Evoluções posteriores ao v1

Com o publication gate já aprovado, permanecem como evoluções futuras:

- Orchestrator para workflows multi-profile;
- Villaz Terminal e expansão da experiência de CLI;
- Base Fiscal + RAG;
- Villaz Code;
- hot reload versionado, se houver necessidade normativa;
- observabilidade ampliada sem exposição de dados sensíveis.
