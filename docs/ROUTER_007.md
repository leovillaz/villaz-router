# ROUTER-007 — Reconciliação implementação × especificação

## Objetivo

Eliminar divergências estruturais identificadas entre a especificação consolidada ROUTER-001–006 e o repositório, antes da continuação do algoritmo do Router v1.

## Baseline

O ciclo partiu do commit:

```text
e7e45a0348646b0680033e0050ef1202289262cc
```

## Correções realizadas

### Security / Code Review

`ROUTE-REVIEW-001` depende do intent route-capable `review-security`.

O domínio `security` permanece responsável por classificar o assunto técnico de segurança, mas não seleciona isoladamente `code-review-security`. Evidências de ação de revisão, auditoria ou procura de vulnerabilidades pertencem ao intent `review-security`; evidências do assunto de segurança permanecem no domínio.

Essa separação Domain × Intent cobre casos como:

- `Existe SQL Injection neste trecho C#?`;
- `Analise a segurança deste código Flutter.`;
- `Este endpoint pode vazar dados pessoais?`.

### Contrato de decisão

`RouteDecision` agora rejeita:

- razão incompatível com o estado;
- candidatos em decisões bem-sucedidas;
- `conflict_resolved=true` fora de uma decisão `routed`.

### Validação do ruleset

A validação semântica agora também exige:

- IDs não vazios e com formato controlado;
- `schema_version` e `ruleset_version` bem formados;
- `strong > medium > weak`;
- `minimum_score` como threshold agregado, inclusive acima de uma evidência `strong`;
- prioridades duplicadas permitidas entre rotas habilitadas;
- nenhuma rota habilitada para profile desabilitado;
- comparação de evidências duplicadas com NFKC, case folding, whitespace e accent folding.

### Matriz de regressão

RT-001–RT-048 foi versionada em:

```text
tests/regression/router_v1_cases.json
```

A suíte valida:

- presença e ordem dos 48 IDs;
- campos normativos obrigatórios;
- seleção manual e perfil inválido;
- dez repetições previstas para RT-045–RT-048.

## Resultado de validação

```text
52 passed
```

Ambiente desta validação:

```text
Python 3.13.5
pytest 9.1.1
pydantic 2.13.4
PyYAML 6.0.3
```

O requisito do pacote permanece Python 3.13 ou superior.

## Limite explícito

Os 52 testes não significam que RT-001–RT-048 já executam o comportamento do Router. A matriz está versionada e validada como contrato, mas os módulos de normalização, matching, scoring e decisão ainda não foram implementados.

Nenhuma integração com FastAPI, Dispatcher, Ollama ou Villaz Code foi iniciada.

## Próximo passo

Prosseguir com IMPLEMENTAÇÃO-001.05:

1. canonicalização semântica;
2. JSON determinístico UTF-8;
3. SHA-256 lógico;
4. `RulesetSnapshot`.

Depois, implementar classificação e decisão até que os 48 casos possam ser executados comportamentalmente.
