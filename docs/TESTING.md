# Testes

## Comando principal

Com o projeto instalado com o extra de desenvolvimento:

```bash
python -m pytest -q
```

O caminho do interpretador varia entre plataformas. Use `.venv/bin/python` em ambientes POSIX ou `.venv\Scripts\python.exe` no PowerShell quando precisar selecionar explicitamente o venv.

## Evidência corrente

O baseline completo corrente, executado no host Linux autoritativo após o hardening local, é:

```text
914 passed in 2.59s
```

Esse gate terminou sem failures ou erros de collection, e nenhum skip ou xfail inesperado foi reportado.

O baseline completo anterior ao Public Release Hardening foi:

```text
893 passed in 2.43s
```

Esse gate anterior terminou sem failures, skips, xfails, warnings do pytest ou erros de collection.

Durante o hardening de packaging e CLI, um gate focado aprovou `61 testes`. Esse resultado é evidência incremental e não substitui o baseline completo corrente.

O baseline histórico anterior de `707 passed` foi posteriormente substituído por `893 passed in 2.43s`, que por sua vez foi sucedido pelo baseline corrente de 914 testes.

## Categorias

### Testes unitários

Cobrem, entre outros contratos:

- modelos e validação estrutural;
- normalização, matching, scoring e elegibilidade;
- decisão determinística e estados do Router;
- Profile Registry, Dispatcher e Runtime Compatibility;
- bootstrap e lifecycle;
- adapter HTTP, limites e mapeamento de erros;
- configuração, transporte e executor Ollama;
- CLI, package resources e invariantes arquiteturais.

### Integração hermética

Os testes integrados usam configuração, Router, Dispatcher, Registry e requests de execução reais, substituindo somente boundaries externos quando necessário.

O caso normativo RT-017/Unity percorre:

```text
HTTP
  → Router
  → Dispatcher / Profile Registry
  → OllamaExecutionRequest
  → boundary Ollama simulado
  → PromptResponse
```

Nenhum servidor Ollama, socket, GPU ou internet é necessário para essa validação.

### Packaging e CLI

A cobertura focada verifica:

- presença e equivalência lógica dos YAMLs empacotados;
- resolução por `importlib.resources` independente do cwd e de `.git`;
- lifetime do recurso durante a execução do servidor;
- precedência total de `--configuration-root`;
- defaults `127.0.0.1:8000`;
- entrypoints de console e módulo;
- integração com `uvicorn.run` simulada;
- warning de exposição para host não-loopback.

### Testes operacionais com Ollama

A validação real permanece separada da suíte hermética e foi executada com sucesso no deployment Linux de referência e em uma instalação independente em VM Debian 13.

Evidências operacionais aprovadas incluem:

- health local e remoto;
- `POST /v1/prompt` com modelo real;
- `Restart=on-failure` sob falha abrupta;
- autostart via `systemd`;
- persistência da política LAN-only em `nftables`;
- reboot acceptance no host de referência;
- clean install third-party sem checkout Git no runtime;
- deployment third-party com serviço dedicado e firewall;
- reboot acceptance na VM third-party;
- inferência remota pós-reboot com `profile=code-review-security`, `model=qwen2.5-coder:14b` e `state=explicit`.

Os outputs textuais do modelo podem variar e não fazem parte da suíte hermética normal.

## Gates

### Mudança local focada

Execute apenas os testes diretamente relacionados e as validações estáticas proporcionais ao escopo.

### Suíte completa

No publication gate:

```bash
python -m pytest -q
```

O resultado aprovado está registrado na seção de evidência corrente. Novos resultados devem ser registrados somente depois da execução efetiva de cada gate.

### Artefatos de distribuição

Wheel, lock e `SHA256SUMS` foram validados por SHA-256 e reproduzidos em clean install third-party durante a `IMPLEMENTAÇÃO-002.11`. Como a futura release deve corresponder ao estado exato da tag, qualquer alteração que afete o conteúdo do wheel exige reconstrução do artefato candidato, nova inspeção, novos hashes e nova validação antes da publicação.

### Publication gate

O publication gate do Public Release Hardening foi aprovado e reuniu:

- suíte completa;
- build de wheel e sdist;
- inspeção dos artefatos;
- clean install;
- validações de segurança e supply chain;
- reprodução operacional aprovada;
- revisão explícita do conteúdo a publicar.

Esse gate permanece historicamente concluído. A futura tag/GitHub Release exige apenas validar novamente o conjunto exato de artefatos produzido a partir do estado final versionado, sem reabrir o publication gate arquitetural.

## CI

O workflow oficial `.github/workflows/tests.yml` foi validado remotamente no GitHub Actions sobre o commit `b072d673de99026785f333ab7fdb27610bb1ec51` e terminou com sucesso. Os jobs `source-validation` e `distribution-validation` concluíram integralmente; o segundo incluiu build de wheel/sdist, inspeção dos artefatos e validação do wheel instalado.

O GitHub Private Vulnerability Reporting também foi confirmado habilitado pelo operador. Esses requisitos não são pendências da primeira release.

Os testes automatizados normais permanecem herméticos e não exigem Ollama real. O E2E operacional com Ollama e modelos reais já foi executado como gate separado. Testes adicionais de deployment e portabilidade pertencem à `IMPLEMENTAÇÃO-002.11`.

O requisito declarado é Python 3.13 ou superior, mas a matriz CI atual cobre somente Python 3.13. Compatibilidade com versões posteriores ainda não é validada pela CI.
