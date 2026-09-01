# Villaz Router

Router determinístico e auditável para selecionar perfis especializados e executar prompts em modelos locais via Ollama. Nenhum LLM participa da decisão de roteamento.

O projeto está em hardening pré-publicação. O baseline completo corrente, validado no host Linux autoritativo após o hardening local, é `914 passed in 2.59s`; o baseline anterior ao hardening foi `893 passed in 2.43s`. O hardening de CI e supply chain está implementado e validado localmente, mas a execução remota no GitHub depende da publicação do commit.

Os gates finais de distribuição e publicação permanecem pendentes.

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

## Quickstart

```bash
git clone https://github.com/leovillaz/villaz-router
cd villaz-router

python -m venv .venv
python -m pip install -e .
villaz-router serve
```

O comando equivalente é:

```bash
python -m villaz_router serve
```

Por padrão, o servidor escuta em `127.0.0.1:8000` e usa somente a configuração empacotada. Consulte o [guia de instalação](docs/INSTALLATION.md) para preparar o Ollama e os modelos.

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

O bind padrão é loopback. `--host 0.0.0.0` é opt-in e pode expor a API, que neste estágio não possui autenticação como mecanismo de proteção. O projeto não deve registrar prompts, respostas, system prompts ou configuração sensível.

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
