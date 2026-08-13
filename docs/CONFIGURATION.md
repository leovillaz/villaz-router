# Configuração do Router

Arquivo:

```text
config/router.yaml
```

Configuração oficial v1:

```yaml
schema_version: "1.0"

router:
  engine:
    expected_major_version: 1

  scoring:
    strong: 10
    medium: 4
    weak: 1

  eligibility:
    minimum_score: 10
    weak_only_cannot_qualify: true

  ambiguity:
    minimum_margin: 5

  normalization:
    unicode_nfkc: true
    lowercase: true
    lowercase_locale_independent: true
    collapse_whitespace: true
    accent_insensitive_matching: true

  lifecycle:
    ruleset_reload: startup_only
    immutable_snapshot_per_instance: true

  integrity:
    algorithm: sha256
    canonical_format: deterministic_json_utf8

  privacy:
    store_full_message: false
    store_evidence: true
```

## Scoring

| Strength | Pontos |
|---|---:|
| strong | 10 |
| medium | 4 |
| weak | 1 |

## Elegibilidade

`minimum_score = 10`

Evidências exclusivamente `weak` não podem tornar um candidato elegível, mesmo se a soma atingir o threshold.

## Ambiguidade

`minimum_margin = 5`

A margem é aplicada apenas depois das precedências semânticas.

## Lifecycle

Não há hot reload no Router v1.

## Integridade

O formato aprovado para identidade lógica é SHA-256 sobre representação canônica em JSON determinístico UTF-8. A implementação dessa etapa é a próxima fase do projeto.
