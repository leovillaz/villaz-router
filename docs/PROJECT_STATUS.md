# Status do projeto

## Estado público atual

O Villaz Router v1 está funcionalmente implementado:

- Router determinístico e matriz normativa RT-001–RT-048;
- Profile Registry e Dispatcher;
- Runtime Compatibility e Application Bootstrap;
- configuração operacional oficial;
- camada Ollama Execution;
- API FastAPI com lifecycle, health endpoints e `POST /v1/prompt`;
- fluxo HTTP → Router → Dispatcher/Profile Registry → Ollama → HTTP;
- CLI `villaz-router serve` e equivalente por `python -m`;
- configuração canônica disponível como package resources;
- override externo explícito e integral;
- Apache License 2.0 materializada no source tree.

Nenhum LLM participa da decisão de roteamento.

## Validação

O baseline completo corrente, executado no host Linux autoritativo após o hardening local, é:

```text
914 passed in 2.59s
```

Esse gate não teve failures nem erros de collection, e nenhum skip ou xfail inesperado foi reportado.

O baseline completo anterior ao Public Release Hardening foi:

```text
893 passed in 2.43s
```

Esse gate anterior não teve failures, skips, xfails, warnings do pytest ou erros de collection. Durante o hardening de packaging e CLI, um gate focado separado também aprovou `61 testes`; essa evidência incremental não substitui o baseline completo corrente de 914 testes.

A integração vertical RT-017/Unity foi validada de forma hermética usando Router, Dispatcher, Profile Registry e `OllamaExecutionRequest` reais, com substituição somente do boundary final do executor. A suíte automatizada normal não exige Ollama real.

## Publication readiness

Estado geral:

```text
NOT_READY_FOR_PUBLICATION
```

O código funcional está concluído. O hardening de CI e supply chain está implementado e validado localmente, com Actions fixadas por SHA, permissões somente de leitura, validação separada de source e distribuição, `pip check`, build de wheel/sdist, instalação isolada do wheel e Dependabot para pip e GitHub Actions. A execução remota desse workflow depende da publicação do commit.

A preparação pública ainda depende de:

- commit e push autorizados;
- clean clone e clean install final;
- validação final de wheel/sdist no estado publicado;
- GitHub Private Vulnerability Reporting efetivamente habilitado e validado;
- E2E operacional com Ollama;
- gate explícito de publicação.

A licença Apache 2.0 e os metadados públicos estão materializados localmente, mas isso não representa uma publicação ou release concluída.

## Próximo passo

Concluir Public Release Hardening e executar o publication gate. Consulte [ROADMAP.md](ROADMAP.md) e [TESTING.md](TESTING.md).
