# Instalação

O Villaz Router requer Python 3.13 ou superior. Uvicorn é uma dependência normal de runtime e é instalado junto com o projeto.

Ollama é um serviço externo. O projeto não instala Ollama, não baixa modelos e não executa model pull automaticamente.

## A. Desenvolvimento a partir do clone

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

## B. Instalação como distribuição Python

A instalação não editável diretamente do diretório do projeto é:

```bash
python -m pip install .
```

O metadata do projeto também está preparado para wheel e sdist, mas o build e o clean install desses artefatos ainda pertencem ao gate de distribuição. Não há publicação PyPI nem validação final de artefato declarada neste estágio.

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
