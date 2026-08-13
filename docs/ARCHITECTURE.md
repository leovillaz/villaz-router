# Arquitetura

## Visão geral

O Villaz Router é um núcleo determinístico e isolado.

```text
RouteRequest
    |
    v
Router
    |
    +--> regras declarativas
    +--> normalização
    +--> evidências
    +--> intents/domains
    +--> routes
    |
    v
RouteDecision
```

Integrações externas não pertencem ao core:

```text
API
 |
 v
Router
 |
 v
Dispatcher / Profile Registry
 |
 v
Ollama
```

## Separação de responsabilidades

### Configuração

`config/router.yaml`

Define parâmetros normativos do engine:

- scoring;
- elegibilidade;
- margem;
- normalização;
- lifecycle;
- integridade;
- privacidade.

### Profiles

`rules/profiles.yaml`

Catálogo de perfis válidos.

### Domains

`rules/domains.yaml`

Classificação técnica baseada em evidências.

### Intents

`rules/intents.yaml`

Classificação de intenção. Apenas intents com `route_capable: true` podem participar de condições de rota.

### Routing

`rules/routing.yaml`

É o único artefato que associa condições semânticas a perfis.

```text
EVIDENCE
   ↓
INTENT / DOMAIN
   ↓
ROUTE
   ↓
PROFILE
```

## Estados finais do Router

- `explicit`
- `routed`
- `ambiguous`
- `unrouted`

Regras:

- `explicit` e `routed` exigem perfil;
- `ambiguous` e `unrouted` exigem `profile = null`;
- não há fallback genérico;
- ambiguidade é resultado legítimo.

## Determinismo

O comportamento deve depender apenas de:

- request;
- configuração;
- ruleset ativo.

Não podem servir como desempate implícito:

- posição física no YAML;
- ordem de detecção;
- ordem alfabética;
- nome de profile;
- filesystem.

## Lifecycle

O ruleset v1 é:

```text
startup_only
```

A instância usa um snapshot imutável durante toda a execução. Alterações em disco só entram em vigor após reinicialização controlada.
