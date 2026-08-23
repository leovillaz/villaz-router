# Villaz Router

Router determinístico, declarativo e auditável para seleção de perfis especializados no projeto **Villaz-Lab**.

> **Status:** Router determinístico v1 implementado e validado comportamentalmente. A `VALIDAÇÃO-001.09` fechou o Router com 228 testes, e a `IMPLEMENTAÇÃO-002.02` implementou e validou tecnicamente o Profile Registry. Suíte atual: 333 testes. Próxima etapa: Dispatcher e validação de compatibilidade de runtime.

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
- `match_evidence` e `match_evidence_set` recebem a mensagem já normalizada em `normalized_message`; `evidence.value` é normalizado internamente pelo matcher;
- validação fail-fast de evidência que normalize para vazio;
- scoring determinístico baseado em `EvidenceStrength` e `ScoringConfig`;
- resultado estruturado por `EvidenceContribution` e `ScoringResult`;
- validações fail-fast de integridade entre `EvidenceMatch` e `Evidence`;
- API pública `score_evidence_matches`;
- elegibilidade por `minimum_score` e weak-only gate;
- avaliação determinística de Domains e Intents;
- qualificação estrutural de Routes;
- gate de conflito entre múltiplos Intents `route_capable`;
- precedência por maior `priority`;
- resolução por `comparison_score` e `minimum_margin`;
- estados finais `explicit`, `routed`, `ambiguous` e `unrouted`;
- candidatos ambíguos canônicos por score decrescente e `route_id` crescente;
- `RouteCandidate` e `RouteDecision` com invariantes de estado;
- API pública `decide_route`;
- Profile Registry com `ProfileDefinition`, `ProfileRegistrySnapshot`, erros próprios, loader YAML, canonicalização e `registry_hash` determinístico;
- APIs públicas do Registry exportadas pelo pacote `villaz_router`;
- suíte atual com 333 testes.

Próxima etapa planejada:

- implementar o Dispatcher;
- implementar `validate_runtime_compatibility()` entre Router e Profile Registry;
- manter `profiles/profiles.yaml` oficial pendente até a definição de modelos e `system_prompt` operacionais reais.

Depois virão FastAPI, integração com Ollama e a validação do fluxo vertical completo. Consulte [docs/ROUTER_007.md](docs/ROUTER_007.md).

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
