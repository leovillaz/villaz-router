# Status do projeto

## Estado público atual

O Villaz Router v1 está funcionalmente implementado e o repositório está público:

- Router determinístico e matriz normativa RT-001–RT-048;
- Profile Registry e Dispatcher;
- Runtime Compatibility e Application Bootstrap;
- configuração operacional oficial;
- camada Ollama Execution;
- API FastAPI com lifecycle, health endpoints e `POST /v1/prompt`;
- fluxo HTTP → Router → Dispatcher/Profile Registry → Ollama → HTTP;
- CLI `villaz-router serve` e equivalente por `python -m`;
- configuração canônica disponível como package resources;
- override externo explícito e integral;
- Apache License 2.0 materializada no source tree.

Nenhum LLM participa da decisão de roteamento.

## Validação

O baseline completo corrente, executado no host Linux autoritativo após o hardening local, é:

```text
914 passed in 2.59s
```

Esse gate não teve failures nem erros de collection, e nenhum skip ou xfail inesperado foi reportado.

O baseline completo anterior ao Public Release Hardening foi:

```text
893 passed in 2.43s
```

Esse gate anterior não teve failures, skips, xfails, warnings do pytest ou erros de collection. Durante o hardening de packaging e CLI, um gate focado separado também aprovou `61 testes`; essa evidência incremental não substitui o baseline completo corrente de 914 testes.

A integração vertical RT-017/Unity foi validada de forma hermética usando Router, Dispatcher, Profile Registry e `OllamaExecutionRequest` reais, com substituição somente do boundary final do executor. A suíte automatizada normal não exige Ollama real.

## Validação operacional

A reprodução operacional foi validada além da suíte hermética:

- deployment Linux de referência com `systemd`, health checks, Ollama real e exposição LAN-only controlada por `nftables`;
- `Restart=on-failure` validado para falha abrupta do processo principal;
- reboot acceptance validado sem `systemctl start` manual;
- instalação limpa em VM Debian 13 sem checkout Git no runtime;
- wheel, lock e artefatos transferidos/verificados por SHA-256 durante o gate de clean install;
- serviço dedicado `villaz-router`, runtime isolado em `/opt/villaz-router` e autostart validados;
- exposição TCP/8000 na VM restrita a loopback e `192.168.15.0/24`, com demais origens para essa porta bloqueadas;
- após reboot real da VM, `/health/live`, `/health/ready` e `POST /v1/prompt` responderam HTTP 200 remotamente a partir de `192.168.15.118`;
- a inferência pós-reboot confirmou `profile=code-review-security`, `model=qwen2.5-coder:14b` e `state=explicit`;
- contador `nftables` e journal confirmaram tráfego LAN externo real após o reboot.

## GitHub publication readiness

Também estão validados:

- workflow oficial `.github/workflows/tests.yml` executado por `push` no commit `b072d673de99026785f333ab7fdb27610bb1ec51` com `conclusion=success`;
- job `source-validation` concluído com sucesso;
- job `distribution-validation` concluído com sucesso, incluindo build de wheel/sdist, inspeção dos artefatos e validação do wheel instalado;
- GitHub Private Vulnerability Reporting confirmado habilitado no repositório.

## Estado de publicação e distribuição

```text
PUBLIC_REPOSITORY = TRUE
PUBLIC_RELEASE_HARDENING = COMPLETE
PUBLICATION_GATE = COMPLETE
LINUX_REFERENCE_DEPLOYMENT = VALIDATED
THIRD_PARTY_CLEAN_INSTALL = VALIDATED
THIRD_PARTY_DEPLOYMENT = VALIDATED
INITIAL_VERSIONED_RELEASE = PENDING
```

O repositório já foi aberto ao público, com a licença Apache 2.0 publicada. O Public Release Hardening e o publication gate foram concluídos. O workflow oficial `.github/workflows/tests.yml` foi executado com sucesso no estado publicado, incluindo `source-validation` e `distribution-validation`, e o GitHub Private Vulnerability Reporting foi confirmado habilitado.

O deployment Linux de referência foi validado com runtime em `/opt/villaz-router/.venv`, usuário/grupo `villaz-router`, systemd, autostart, `Restart=on-failure`, stop administrativo sem restart, bind `0.0.0.0:8000` protegido por nftables LAN-only, health live/ready, reboot acceptance e inferência real após reboot.

A instalação e o deployment third-party também foram validados em VM Debian 13 independente, sem checkout Git no runtime. Wheel e lock foram verificados por SHA-256, a instalação foi reproduzida com `--require-hashes` e wheel `--no-deps`, o serviço permaneceu ativo após reboot e os endpoints `/health/live`, `/health/ready` e `POST /v1/prompt` responderam HTTP 200 remotamente pela LAN. A inferência pós-reboot confirmou `profile=code-review-security`, `model=qwen2.5-coder:14b` e `state=explicit`.

A atividade atual é `IMPLEMENTAÇÃO-002.11 — Operational Deployment & Portability`. Permanecem pendentes:

- materializar e publicar os artefatos da primeira GitHub Release;
- criar a tag e a release inicial;
- Windows nativo e WSL2;
- Docker/Compose;
- documentação e gate final de deployment/portabilidade.

## Próximo passo

Fechar a `IMPLEMENTAÇÃO-002.11`, reconciliar o estado exato candidato à primeira release e, após aprovação explícita, materializar a tag/GitHub Release inicial. Consulte [ROADMAP.md](ROADMAP.md) e [TESTING.md](TESTING.md).
