# Desenvolvimento

## Ambiente

Requisito: Python 3.13 ou superior.

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

Ative o ambiente usando o comando apropriado para a plataforma:

- POSIX: `source .venv/bin/activate`;
- PowerShell: `.venv\Scripts\Activate.ps1`.

Não trate `.venv/bin/python` como caminho universal. Quando o venv estiver ativo, prefira `python -m ...`.

## Estrutura principal

```text
src/villaz_router/
├── __init__.py
├── __main__.py
├── cli.py
├── runtime_resources.py
├── runtime_data/
│   ├── config/
│   ├── profiles/
│   └── rules/
├── bootstrap.py
├── bootstrap_models.py
├── bootstrap_errors.py
├── router.py
├── models.py
├── config.py
├── loader.py
├── validation.py
├── normalization.py
├── matcher.py
├── scoring.py
├── eligibility.py
├── registry_loader.py
├── registry_models.py
├── registry_canonical.py
├── registry_errors.py
├── dispatcher.py
├── dispatcher_models.py
├── dispatcher_errors.py
├── runtime_compatibility.py
├── runtime_compatibility_errors.py
├── http_api/
│   ├── app.py
│   ├── body_limit.py
│   ├── dependencies.py
│   ├── models.py
│   ├── router_adapter.py
│   └── routes.py
└── ollama_execution/
    ├── config.py
    ├── config_loader.py
    ├── errors.py
    ├── executor.py
    ├── factory.py
    ├── httpx2_transport.py
    ├── models.py
    └── transport.py
```

Responsabilidades:

- `cli.py` e `__main__.py`: entrypoints públicos;
- `runtime_resources.py` e `runtime_data/`: resolução e dados operacionais empacotados;
- `router.py`: decisão determinística;
- `registry_*`: catálogo operacional de profiles;
- `dispatcher*`: transformação de decisão despachável em `DispatchPlan`;
- `bootstrap*`: carregamento e compatibilidade do runtime;
- `http_api/router_adapter.py`: fronteira HTTP–Router;
- `http_api/routes.py`: composition boundary com Dispatcher e Ollama;
- `http_api/app.py`: lifecycle da aplicação;
- `ollama_execution/`: execução e transporte isolados.

## Convenções

- mudanças pequenas e determinísticas;
- regras normativas acompanhadas de testes;
- sem fallback, retry ou normalização implícita;
- sem logging de prompts, respostas, system prompts ou configuração sensível;
- núcleo do Router independente de FastAPI, Dispatcher e Ollama;
- YAML validado estrutural e semanticamente;
- package resources mantidos logicamente equivalentes aos YAMLs canônicos da raiz.

## Validação durante o desenvolvimento

Execute os testes focados no escopo da mudança:

```bash
python -m pytest -q tests/unit/caminho_do_teste.py
```

Antes de propor publicação, siga os gates descritos em [TESTING.md](TESTING.md).

## Documentação relacionada

- [Arquitetura](ARCHITECTURE.md)
- [API](API.md)
- [Instalação](INSTALLATION.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Contribuição](../CONTRIBUTING.md)
