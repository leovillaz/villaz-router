# Villaz Router

Router determinístico, declarativo e auditável para seleção de perfis especializados no projeto **Villaz-Lab**.

> **Status:** ruleset, canonicalização, normalização e matching determinístico implementados. A matriz RT-001–RT-048 permanece versionada como contrato; scoring em runtime e algoritmo completo de decisão ainda não foram implementados.

## Objetivos

O Villaz Router foi desenhado para:

- selecionar um único perfil especializado de forma determinística;
- usar regras declarativas em YAML;
- separar classificação de intenção/domínio da seleção de perfil;
- manter decisões reproduzíveis e auditáveis;
- rejeitar rulesets estrutural ou semanticamente inválidos;
- não depender de LLM para decidir o roteamento;
- preservar segurança e privacidade como requisitos transversais.

## Estado atual

Implementado e testado:

- contratos `RouteRequest`, `RouteDecision` e erros internos;
- coerência entre estado, modo, razão, candidatos e conflito;
- modelos formais de configuração e ruleset;
- loader seguro de YAML;
- validação estrutural com Pydantic;
- validação semântica e de referências cruzadas;
- validação de IDs, versões, scoring e profiles desabilitados;
- ruleset oficial v1;
- separação normativa Domain × Intent para Security / Code Review;
- rota `code-review-security` condicionada ao intent `review-security`;
- matriz normativa RT-001–RT-048 em `tests/regression`;
- canonicalização semântica independente da ordem física do YAML;
- JSON determinístico UTF-8;
- hash lógico SHA-256;
- `RulesetSnapshot` imutável integrado ao loader;
- normalização determinística com NFKC, `casefold()`, remoção de diacríticos e colapso de whitespace;
- matching simétrico de evidências `term` e `phrase`;
- fronteiras formais de `term` com letras Unicode, números e `_` como caracteres de palavra;
- `EvidenceMatch` imutável com posição da primeira ocorrência válida;
- matching agregado determinístico ordenado por `evidence_id`;
- validação fail-fast de evidência que normalize para vazio;
- suíte atual com 97 testes.

Próxima etapa planejada:

- scoring determinístico em runtime.

Depois virão execução comportamental de RT-001–RT-048 e algoritmo final de decisão. Consulte [docs/ROUTER_007.md](docs/ROUTER_007.md).

## Requisitos

- Linux
- Python 3.13+
- Git
- `python3-venv`
- `pip`

Ambiente usado durante o desenvolvimento inicial:

- Python 3.13.5
- Git 2.47.3

## Instalação rápida

```bash
git clone <URL_DO_REPOSITORIO>
cd villaz-router

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev]"

pytest -v
```

Consulte [docs/INSTALLATION.md](docs/INSTALLATION.md) para o procedimento completo.

## Estrutura

```text
villaz-router/
├── config/
│   └── router.yaml
├── rules/
│   ├── profiles.yaml
│   ├── domains.yaml
│   ├── intents.yaml
│   └── routing.yaml
├── src/
│   └── villaz_router/
├── tests/
│   ├── unit/
│   └── regression/
├── docs/
├── .github/
│   └── workflows/
├── pyproject.toml
└── README.md
```

## Pipeline do ruleset

```text
YAML
  ↓
safe_load
  ↓
validação estrutural
  ↓
validação semântica
  ↓
canonicalização semântica
  ↓
JSON determinístico UTF-8
  ↓
SHA-256 lógico
  ↓
RulesetSnapshot imutável
  ↓
Router
```

## Perfis oficiais v1

- `mobile-dev`
- `unity-dev`
- `docs-dev`
- `fiscal-finance`
- `code-review-security`

## Precedência das rotas v1

| Prioridade | Rota | Perfil |
|---:|---|---|
| 500 | review-security | `code-review-security` |
| 450 | fiscal | `fiscal-finance` |
| 400 | documentation | `docs-dev` |
| 300 | unity | `unity-dev` |
| 200 | mobile | `mobile-dev` |

A seleção manual de perfil tem precedência sobre o roteamento automático.

## Documentação

- [Instalação](docs/INSTALLATION.md)
- [Guia de replicação](docs/REPLICATION_GUIDE.md)
- [Arquitetura](docs/ARCHITECTURE.md)
- [Configuração](docs/CONFIGURATION.md)
- [Referência do ruleset](docs/RULESET_REFERENCE.md)
- [Desenvolvimento](docs/DEVELOPMENT.md)
- [Testes](docs/TESTING.md)
- [Status do projeto](docs/PROJECT_STATUS.md)
- [Roadmap](docs/ROADMAP.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Segurança](SECURITY.md)
- [Contribuição](CONTRIBUTING.md)

## Segurança e privacidade

O Router não deve registrar automaticamente a mensagem integral do usuário. O ruleset oficial v1 usa:

```yaml
privacy:
  store_full_message: false
  store_evidence: true
```

Veja [SECURITY.md](SECURITY.md).

## Licença

A licença pública ainda deve ser escolhida antes da abertura do repositório. Enquanto o repositório permanecer privado, não há licença pública concedida por este projeto.
