# Testes

## Execução

```bash
python -m pytest -v
```

## Estado atual

A suíte corrente possui **384 testes**. O checkpoint histórico `VALIDAÇÃO-001.09` permanece registrado com `228 passed`, e o fechamento técnico do Profile Registry permanece historicamente registrado com `333 passed`.

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
- execução comportamental integral de RT-001–RT-048 contra `decide_route()`;
- determinismo de RT-045–RT-048 com 10 repetições por caso;
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
- exportação pública de `decide_route`;
- contratos e imutabilidade de `ProfileDefinition`;
- validação estrita de IDs, booleanos e strings obrigatórias do Profile Registry;
- contratos e imutabilidade de `ProfileRegistrySnapshot`;
- resolução exata por `get()`, `contains()` e `list_profiles()`;
- domínio próprio de erros do Registry;
- canonicalização determinística do Registry;
- ordem física de profiles no YAML sem efeito no `registry_hash`;
- alterações semânticas e whitespace válido alterando o `registry_hash`;
- serialização UTF-8 compacta sem normalização destrutiva;
- loader de `profiles/profiles.yaml` e classificação determinística de erros;
- cobertura integrada loader → definição → canonicalização → snapshot;
- exports públicos do Profile Registry.
- contratos, imutabilidade e validações de `DispatchPlan`;
- domínio próprio de erros do Dispatcher;
- construção determinística de planos para estados `routed` e `explicit`;
- rejeição de `ambiguous` e `unrouted` sem consulta ao Registry;
- tradução de `PROFILE_NOT_FOUND` preservando a causa original;
- rejeição de profiles desabilitados sem fallback;
- tradução restrita de `ValidationError` na construção final do plano;
- propagação de erros inesperados sem mascaramento;
- determinismo de `build_dispatch_plan`;
- exports públicos do Dispatcher;
- proteção da direção arquitetural Router + Registry → Dispatcher.

## Matriz normativa

A matriz aprovada está em:

```text
tests/regression/router_v1_cases.json
```

Os testes atuais validam os 48 casos como artefato normativo: IDs, campos, seleção manual, perfil inválido e repetições de determinismo.

O pipeline runtime de normalização, matching, scoring, elegibilidade e decisão está implementado. RT-001–RT-048 são validados tanto como artefato normativo quanto comportamentalmente contra `decide_route()`. RT-045–RT-048 são executados 10 vezes cada para verificar determinismo. Profile Registry e Dispatcher também estão implementados e validados. A próxima etapa técnica é a validação de compatibilidade de runtime entre Router e Registry.

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
