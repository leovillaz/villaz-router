# Testes

## Execução

```bash
python -m pytest -v
```

## Estado atual

A suíte documentada possui **180 testes**.

Cobertura atual:

- contratos de request/decision;
- coerência entre estado, modo, razão, candidatos e conflito;
- modelos e imutabilidade do ruleset;
- leitura segura dos YAMLs oficiais;
- YAML inválido, arquivo ausente e documento não-mapping;
- IDs, versões e evidências inválidas;
- referências cruzadas;
- profiles desabilitados;
- prioridades duplicadas aceitas como precedência válida;
- coerência de scoring e threshold agregado;
- `minimum_score` superior a uma evidência `strong` aceito;
- normalização accent-insensitive na validação de duplicatas;
- associação da rota de segurança ao intent `review-security`;
- integridade do contrato RT-001–RT-048;
- canonicalização determinística do ruleset;
- independência da ordem física de profiles, domains, intents, routes e evidências;
- serialização compacta em JSON UTF-8;
- mudanças semânticas alterando o hash;
- reordenação física preservando o hash;
- formato SHA-256 hexadecimal minúsculo;
- criação e estabilidade do `RulesetSnapshot`;
- inclusão das configurações do Router no snapshot;
- integração do snapshot ao loader;
- normalização NFKC + `casefold()` + accent-insensitive + whitespace;
- preservação de pontuação na representação normalizada;
- `EvidenceMatch` congelado e seus invariantes;
- matching de `phrase` por substring literal contínua;
- matching de `term` com fronteiras formais;
- primeira ocorrência válida de uma evidência;
- preservação do valor original da evidência no resultado;
- matching agregado imutável e ordenado deterministicamente por `evidence_id`;
- mensagem vazia resultando em conjunto vazio de matches;
- rejeição semântica de evidência que normalize para vazio;
- contratos e imutabilidade de `EvidenceContribution` e `ScoringResult`;
- invariant `score == soma dos weights`;
- scoring usando exclusivamente pesos de `ScoringConfig`;
- scoring vazio com `score=0` e `contributions=()`;
- independência da ordem física e suporte a generators;
- detecção determinística de IDs duplicados;
- rejeição de `EvidenceMatch` desconhecido;
- validação exata de tipo e valor entre match e evidência configurada;
- ordem fail-fast determinística dos erros de scoring;
- elegibilidade por `minimum_score`;
- weak-only gate e contribuição medium/strong;
- avaliação de todos os Domains e Intents em ordem determinística;
- qualificação estrutural de Routes e resolução exata de referências;
- exclusão de Routes desabilitadas;
- integridade defensiva de profiles;
- conflito entre múltiplos Intents `route_capable`;
- precedência por maior `priority`;
- resolução por `minimum_margin`;
- empate no maior `comparison_score`;
- faixa estrita de candidatos ambíguos;
- ordenação canônica de `RouteCandidate`;
- precedência absoluta de `explicit_profile`;
- perfil explícito inválido ou desabilitado com `INVALID_PROFILE`, sem fallback;
- estado `unrouted`;
- decisões finais `routed` e `ambiguous`;
- semântica de `conflict_resolved`;
- mapeamento determinístico de `RoutingReason`;
- exportação pública de `decide_route`.

## Matriz normativa

A matriz aprovada está em:

```text
tests/regression/router_v1_cases.json
```

Os testes atuais validam os 48 casos como artefato normativo: IDs, campos, seleção manual, perfil inválido e repetições de determinismo.

O pipeline runtime de normalização, matching, scoring, elegibilidade e decisão já está implementado. A próxima etapa é executar e reconciliar comportamentalmente RT-001–RT-048 contra `decide_route()`; até este checkpoint, a matriz continua sendo validada também como artefato normativo.

## Verificações adicionais

```bash
python -m compileall -q src tests
git diff --check
```

## CI

O workflow `.github/workflows/tests.yml`:

- usa Python 3.13;
- desabilita persistência de credenciais no checkout;
- aplica timeout;
- compila os módulos;
- instala o pacote com dependências de desenvolvimento;
- executa `python -m pytest -v`.
