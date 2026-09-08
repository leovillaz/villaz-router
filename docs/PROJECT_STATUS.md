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

## Validação automatizada

O baseline completo corrente, executado no host Linux autoritativo após o hardening local, é:

```text
914 passed in 2.59s
```

Esse gate não teve failures nem erros de collection, e nenhum skip ou xfail inesperado foi reportado.

O baseline completo anterior ao Public Release Hardening foi:

```text
893 passed in 2.43s
```

Durante o hardening de packaging e CLI, um gate focado separado também aprovou `61 testes`; essa evidência incremental não substitui o baseline completo corrente de 914 testes.

A integração vertical RT-017/Unity foi validada de forma hermética usando Router, Dispatcher, Profile Registry e `OllamaExecutionRequest` reais, com substituição somente do boundary final do executor. A suíte automatizada normal não exige Ollama real.

## Validação operacional

A reprodução operacional foi validada além da suíte hermética:

- deployment Linux de referência com `systemd`, health checks, Ollama real e exposição LAN-only controlada por `nftables`;
- `Restart=on-failure` validado para falha abrupta do processo principal;
- reboot acceptance validado sem `systemctl start` manual;
- instalação limpa em VM Debian 13 sem checkout Git no runtime;
- wheel e artefatos transferidos/verificados por SHA-256 durante o gate de clean install;
- serviço dedicado `villaz-router`, runtime isolado em `/opt/villaz-router` e autostart validados;
- exposição TCP/8000 na VM restrita a loopback e `192.168.15.0/24`, com demais origens para essa porta bloqueadas;
- após reboot real da VM, `/health/live`, `/health/ready` e `POST /v1/prompt` responderam HTTP 200 remotamente a partir de `192.168.15.118`;
- a inferência pós-reboot confirmou `profile=code-review-security`, `model=qwen2.5-coder:14b` e `state=explicit`;
- contador `nftables` e journal confirmaram tráfego LAN externo real após o reboot.

## Publication readiness

Estado geral:

```text
PUBLIC_REPOSITORY_RELEASE_GATE_OPEN
```

O repositório já está público e o hardening de distribuição foi publicado na `main`. Os gates de clean install e E2E operacional com Ollama real foram executados com sucesso. Isso não equivale ainda a uma release inicial versionada.

Permanecem para fechamento formal:

- reconciliar e confirmar a execução remota do CI no estado publicado;
- confirmar/validar o GitHub Private Vulnerability Reporting como canal efetivamente disponível;
- executar o publication gate final com a documentação já reconciliada;
- criar a tag e a release inicial quando o gate for aprovado.

## Próximo passo

Fechar os itens restantes de publication readiness e, somente então, materializar a primeira tag/release. Consulte [ROADMAP.md](ROADMAP.md) e [TESTING.md](TESTING.md).
