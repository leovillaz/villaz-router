# Desenvolvimento

## Instalação editável

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Estrutura dos módulos

```text
src/villaz_router/
├── __init__.py
├── config.py
├── errors.py
├── loader.py
├── matcher.py
├── models.py
├── normalization.py
├── router.py
├── scoring.py
└── validation.py
```

No estágio atual:

- `models.py`: contratos e modelos formais;
- `config.py`: modelos de configuração;
- `errors.py`: erros internos;
- `loader.py`: leitura segura e parse;
- `validation.py`: validação semântica, incluindo regras dependentes da normalização oficial;
- `normalization.py`: normalização determinística de mensagens e evidências;
- `matcher.py`: matching determinístico de `term` e `phrase`;
- `scoring.py`: scoring determinístico, validações runtime de integridade e construção de `ScoringResult`;
- `router.py`: reservado para elegibilidade e algoritmo final de decisão.

## Política de implementação

Preferir blocos pequenos, cada um com:

1. alteração limitada;
2. testes;
3. `git diff --check`;
4. commit próprio;
5. working tree limpo.

## Commits iniciais do projeto

A implementação inicial foi organizada em checkpoints:

```text
chore: initialize Villaz Router project
feat: add formal ruleset models
feat: add structural ruleset loader
feat: add semantic ruleset validation
```

Os hashes podem variar em réplicas e forks.
