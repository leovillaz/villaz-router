# Villaz Router

Router determinístico e auditável para selecionar perfis especializados e executar prompts em modelos locais via Ollama. Nenhum LLM participa da decisão de roteamento.

O repositório Villaz Router é público. O Public Release Hardening e o publication gate foram concluídos, com baseline completo de `914 passed in 2.59s`.

A `IMPLEMENTAÇÃO-002.11 — Operational Deployment & Portability` validou o deployment Linux de referência e uma instalação limpa em VM Debian 13, incluindo systemd, política LAN-only com nftables, persistência após reboot, health checks e inferência HTTP remota com Ollama real. A primeira tag/GitHub Release e os artefatos públicos versionados ainda não foram publicados.

## Como funciona

```text
HTTP
  → PromptRequest
  → HTTP Router adapter
  → Router determinístico
  → Dispatcher / Profile Registry
  → OllamaExecutionRequest
  → OllamaExecutor
  → PromptResponse
```

Principais características:

- regras declarativas em YAML;
- estados de roteamento `explicit`, `routed`, `ambiguous` e `unrouted`;
- Profile Registry e Dispatcher determinísticos;
- bootstrap fail-fast, sem fallback ou retry implícito;
- API FastAPI com limites e respostas públicas seguras;
- execução Ollama isolada do núcleo de roteamento;
- configuração operacional empacotada e override externo explícito;
- testes automatizados herméticos, sem exigir Ollama real.

## Requisitos

- Python 3.13 ou superior; a matriz CI atual cobre somente Python 3.13, e versões posteriores ainda não são validadas pela CI;
- Ollama instalado e administrado separadamente;
- modelos referenciados pelos profiles já disponíveis no Ollama para execução real.

O Router não exige GPU. Os requisitos de CPU, memória e VRAM dependem do modelo, da quantização, do contexto e do backend.

## Instalação

O fluxo de distribuição por artefatos versionados foi validado durante a `IMPLEMENTAÇÃO-002.11`. A futura GitHub Release fornecerá o wheel `villaz_router-<versão>-py3-none-any.whl`, o lock `requirements-linux-py313.lock` e `SHA256SUMS`; esses artefatos ainda não estão publicados.

Para trabalhar a partir do source tree, consulte o [guia de desenvolvimento](docs/DEVELOPMENT.md). O contrato de instalação, incluindo o fluxo de release candidate, preparação do Ollama e inicialização da API, está no [guia de instalação](docs/INSTALLATION.md).

## Primeiro prompt

```bash
curl -X POST http://127.0.0.1:8000/v1/prompt \
  -H "Content-Type: application/json" \
  -d '{"message":"Meu Rigidbody está se movimentando de forma irregular."}'
```

A resposta pública contém somente:

```json
{
  "response": "Resposta produzida pelo modelo.",
  "profile": "unity-dev",
  "model": "qwen2.5-coder:14b",
  "state": "routed",
  "route_id": "ROUTE-UNITY-001"
}
```

O texto de `response` é gerado pelo modelo e pode variar. O contrato HTTP completo, incluindo validação, limites e erros, está em [docs/API.md](docs/API.md).

## Configuração avançada

Para substituir integralmente os recursos empacotados:

```bash
villaz-router serve --configuration-root /caminho/para/configuracao
```

A árvore externa precisa estar completa. Não há merge nem fallback para os recursos empacotados.

## Segurança

O bind padrão é loopback. `--host 0.0.0.0` é opt-in e pode expor a API, que neste estágio não possui autenticação como mecanismo de proteção. Em deployments LAN-only validados, a exposição deve ser restringida externamente por firewall; não trate o bind em `0.0.0.0` como fronteira de segurança. O projeto não deve registrar prompts, respostas, system prompts ou configuração sensível.

Consulte [SECURITY.md](SECURITY.md) para a política de segurança.

## Documentação

- [Instalação](docs/INSTALLATION.md)
- [Contrato da API](docs/API.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Testes](docs/TESTING.md)
- [Desenvolvimento](docs/DEVELOPMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Guia de replicação](docs/REPLICATION_GUIDE.md)
- [Status do projeto](docs/PROJECT_STATUS.md)
- [Roadmap](docs/ROADMAP.md)
- [Configuração](docs/CONFIGURATION.md)
- [Referência do ruleset](docs/RULESET_REFERENCE.md)

## Contribuição e licença

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) antes de propor alterações.

Copyright 2026 Leandro Vilela. Distribuído sob a [Apache License 2.0](LICENSE).
