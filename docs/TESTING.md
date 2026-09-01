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

A validação real é um gate separado. Ela requer:

- Ollama ativo;
- todos os modelos referenciados já disponíveis;
- recursos de CPU/memória ou GPU adequados;
- decisão explícita de executar chamadas reais.

Os outputs podem variar. Esse gate não deve ser misturado à suíte hermética normal.

## Gates

### Mudança local focada

Execute apenas os testes diretamente relacionados e as validações estáticas proporcionais ao escopo.

### Suíte completa

Antes do publication gate:

```bash
python -m pytest -q
```

O resultado precisa ser registrado como nova evidência somente depois de efetivamente concluir o gate.

### Artefatos de distribuição

Wheel e sdist, conteúdo de package data e clean install serão validados no gate próprio. Essa validação ainda não está declarada como concluída.

### Publication gate

O gate final deve reunir:

- suíte completa;
- build de wheel e sdist;
- inspeção dos artefatos;
- clean install;
- validações de segurança e supply chain;
- reprodução operacional aprovada;
- revisão explícita do conteúdo a publicar.

## CI

A CI normal executa testes automatizados herméticos e não exige Ollama real. O hardening está implementado e validado localmente, com source validation e distribution validation separadas; sua execução remota no GitHub depende da publicação do commit. E2E com modelos pertence ao gate operacional separado.

O requisito declarado é Python 3.13 ou superior, mas a matriz CI atual cobre somente Python 3.13. Compatibilidade com versões posteriores ainda não é validada pela CI.
