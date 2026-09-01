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
- [x] hardening de CI e supply chain implementado e validado localmente; execução remota depende da publicação do commit;
- [ ] commit e push autorizados;
- [ ] clean clone e clean install final;
- [ ] validação final de wheel/sdist no estado publicado;
- [ ] GitHub Private Vulnerability Reporting habilitado e validado;
- [ ] E2E operacional com Ollama e modelos reais;
- [ ] publication gate;
- [ ] tag e release inicial;
- [ ] abertura pública do repositório.

## Evoluções posteriores ao v1

Somente após o publication gate:

- Orchestrator para workflows multi-profile;
- Villaz Terminal e expansão da experiência de CLI;
- Base Fiscal + RAG;
- Villaz Code;
- hot reload versionado, se houver necessidade normativa;
- observabilidade ampliada sem exposição de dados sensíveis.
