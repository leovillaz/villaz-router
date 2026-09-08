# Instalação

O Villaz Router requer Python 3.13 ou superior. Uvicorn é uma dependência normal de runtime e é instalado junto com o projeto.

Ollama é um serviço externo. O projeto não instala Ollama, não baixa modelos e não executa model pull automaticamente.

## A. Desenvolvimento a partir do clone — não é a distribuição oficial

Este fluxo é destinado a desenvolvimento, contribuição e replicação a partir do source tree. Ele não representa o caminho oficial de distribuição para usuário final.

Obtenha o código:

```bash
git clone https://github.com/leovillaz/villaz-router
cd villaz-router
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ativação em POSIX:

```bash
source .venv/bin/activate
```

Ativação em PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Instale o projeto em modo editável com dependências de desenvolvimento:

```bash
python -m pip install -e ".[dev]"
```

## B. Distribuição versionada — release candidate

O fluxo de distribuição aprovado prevê estes artefatos em uma futura GitHub Release:

- `villaz_router-<versão>-py3-none-any.whl`;
- `requirements-linux-py313.lock`;
- `SHA256SUMS`.

A matriz atualmente comprovada é Linux x86_64 com CPython 3.13.x.

O fluxo de instalação do release candidate foi validado em ambiente virtual limpo no host de referência e reproduzido em uma VM Debian 13 independente, sem checkout Git no runtime:

```bash
python -m venv .venv
.venv/bin/python -m pip install 'pip==26.2.1'
.venv/bin/python -m pip install \
  --require-hashes \
  -r requirements-linux-py313.lock
.venv/bin/python -m pip install \
  --no-deps \
  villaz_router-<versão>-py3-none-any.whl
.venv/bin/python -m pip check
```

As dependências são instaladas primeiro pelo lock, com versões fixadas e hashes verificados pelo `pip`. Em seguida, o wheel é instalado com `--no-deps` para impedir uma nova resolução de dependências. `SHA256SUMS` permite verificar a integridade dos artefatos da release.

Ollama continua sendo um serviço externo. O Villaz Router não depende de publicação própria no PyPI; nesta baseline, a instalação online das dependências utiliza o índice `https://pypi.org/simple`. Instalação offline não é uma garantia desta fase.

Os artefatos públicos da GitHub Release ainda **não** estão publicados. O fluxo de distribuição foi validado durante a `IMPLEMENTAÇÃO-002.11`, incluindo clean install em ambiente third-party.

## Preparar o Ollama

Instale e administre o Ollama conforme a documentação do fornecedor. Os identificadores distintos atualmente referenciados por `profiles/profiles.yaml` são:

```text
gemma3:12b
qwen2.5-coder:14b
qwen3:14b
```

O operador precisa obter esses modelos no Ollama antes da execução real. Por exemplo:

```bash
ollama pull gemma3:12b
ollama pull qwen2.5-coder:14b
ollama pull qwen3:14b
ollama list
```

O projeto apenas referencia esses identificadores. Ele não distribui nem relicencia os modelos; disponibilidade, licença e termos pertencem aos respectivos fornecedores. Outputs e desempenho dependem de hardware, quantização, contexto, backend e modelo.

O Router não exige GPU. A inferência pode funcionar em CPU, geralmente mais lentamente; memória e VRAM necessárias variam por modelo e quantização.

## Iniciar a API

Com o ambiente ativado:

```bash
villaz-router serve
```

Comando equivalente:

```bash
python -m villaz_router serve
```

Defaults:

- host: `127.0.0.1`;
- port: `8000`;
- configuração: package resources instalados.

Ajuda:

```bash
villaz-router --help
villaz-router serve --help
```

## Configuração default e override

Sem `--configuration-root`, a CLI usa somente os YAMLs empacotados em `villaz_router.runtime_data`.

Para usar uma árvore externa:

```bash
villaz-router serve --configuration-root /caminho/para/configuracao
```

O path é resolvido como absoluto e substitui integralmente a configuração empacotada. Não há merge nem fallback. A raiz externa precisa conter:

```text
config/ollama.yaml
config/router.yaml
profiles/profiles.yaml
rules/domains.yaml
rules/intents.yaml
rules/profiles.yaml
rules/routing.yaml
```

Falhas de bootstrap ou incompatibilidades encerram o startup sem iniciar uma aplicação parcialmente funcional.

## Host e porta

Para escolher outra porta:

```bash
villaz-router serve --port 9000
```

Bind não-loopback é permitido somente por opção explícita:

```bash
villaz-router serve --host 0.0.0.0
```

A API não possui autenticação como mecanismo de proteção neste estágio. Use `0.0.0.0` apenas em um ambiente cuja exposição de rede esteja controlada.

## Verificação

Com o servidor ativo:

```bash
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
```

Readiness valida o estado do `RuntimeContext` e do `OllamaExecutor` no lifespan, sem probe de rede ao Ollama. Consulte [API.md](API.md) para o contrato completo.
