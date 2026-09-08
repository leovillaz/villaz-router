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

A validação real permanece separada da suíte hermética e foi executada com sucesso no deployment Linux de referência e em uma instalação limpa em VM Debian 13.

Evidências operacionais aprovadas incluem:

- health local e remoto;
- `POST /v1/prompt` com modelo real;
- `Restart=on-failure` sob falha abrupta;
- autostart via `systemd`;
- persistência de política LAN-only em `nftables`;
- reboot acceptance;
- clean install sem checkout Git no runtime;
- inferência remota pós-reboot na VM third-party com `profile=code-review-security`, `model=qwen2.5-coder:14b` e `state=explicit`.

Os outputs textuais do modelo podem variar e não fazem parte da suíte hermética normal.

## Gates

### Mudança local focada

Execute apenas os testes diretamente relacionados e as validações estáticas proporcionais ao escopo.

### Suíte completa

Antes de mudanças de release:

```bash
python -m pytest -q
```

O resultado precisa ser registrado como nova evidência somente depois de efetivamente concluir o gate.

### Artefatos de distribuição

Wheel e artefatos utilizados no gate de clean install foram verificados por SHA-256 e instalados em ambiente third-party. Qualquer nova build destinada a uma tag/release deve repetir build, inspeção e instalação limpa no estado exato a ser versionado.

### Publication gate

O gate final deve reunir:

- suíte completa no estado candidato à release;
- build de wheel e sdist do estado candidato;
- inspeção dos artefatos;
- clean install reproduzível;
- validações de segurança e supply chain;
- reprodução operacional aprovada;
- revisão explícita do conteúdo a publicar;
- confirmação do CI remoto e do canal privado de vulnerabilidades.

## CI

O workflow oficial `.github/workflows/tests.yml` foi validado remotamente no GitHub Actions sobre o commit `b072d673de99026785f333ab7fdb27610bb1ec51` e terminou com sucesso. Os jobs `source-validation` e `distribution-validation` concluíram integralmente; o segundo incluiu build de wheel/sdist, inspeção dos artefatos e validação do wheel instalado.

O GitHub Private Vulnerability Reporting também foi confirmado habilitado pelo operador. Esses dois requisitos deixam de ser pendências do publication readiness.

A CI normal executa testes automatizados herméticos e não exige Ollama real. E2E com modelos pertence ao gate operacional separado e já possui evidência manual aprovada.

O requisito declarado é Python 3.13 ou superior, mas a matriz CI atual cobre somente Python 3.13. Compatibilidade com versões posteriores ainda não é validada pela CI.
