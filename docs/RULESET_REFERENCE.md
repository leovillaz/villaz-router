# Referência do ruleset

## Profiles

```yaml
schema_version: "1.0"
ruleset_version: "1.0.0"

profiles:
  - id: mobile-dev
    enabled: true
  - id: unity-dev
    enabled: true
  - id: docs-dev
    enabled: true
  - id: fiscal-finance
    enabled: true
  - id: code-review-security
    enabled: true
```

## Evidence

Cada evidência contém:

```yaml
id: DOMAIN-MOBILE-001
type: term
strength: strong
value: "flutter"
```

Tipos suportados no v1:

- `term`
- `phrase`

Strengths:

- `strong`
- `medium`
- `weak`

Regex não faz parte do Router v1.

## Domains oficiais

- `mobile`
- `unity`
- `fiscal`
- `security`

## Intents oficiais

- `documentation` — route capable
- `review-security` — route capable
- `development` — auxiliar
- `question` — auxiliar

## Routes oficiais

```yaml
routes:
  - id: ROUTE-REVIEW-001
    enabled: true
    priority: 500
    when:
      intent: review-security
    result:
      profile: code-review-security

  - id: ROUTE-FISCAL-001
    enabled: true
    priority: 450
    when:
      domain: fiscal
    result:
      profile: fiscal-finance

  - id: ROUTE-DOC-001
    enabled: true
    priority: 400
    when:
      intent: documentation
    result:
      profile: docs-dev

  - id: ROUTE-UNITY-001
    enabled: true
    priority: 300
    when:
      domain: unity
    result:
      profile: unity-dev

  - id: ROUTE-MOBILE-001
    enabled: true
    priority: 200
    when:
      domain: mobile
    result:
      profile: mobile-dev
```

## Validações semânticas implementadas

O ruleset é rejeitado quando houver, entre outros:

- ID duplicado de profile/domain/intent/route;
- evidence ID duplicado;
- `ruleset_version` divergente;
- `schema_version` divergente;
- major version incompatível;
- route apontando para profile inexistente;
- route apontando para domain inexistente;
- route apontando para intent inexistente;
- route usando intent com `route_capable: false`;
- `profile.id` usado como evidence;
- evidence vazia;
- evidence normalizada duplicada no mesmo alvo.
