# Troubleshooting

Use diagnóstico não destrutivo. Não recrie repositórios, não complete configurações por fallback e não altere dados operacionais antes de identificar a causa.

## `villaz-router` não é reconhecido

Confirme que o ambiente correto está ativo e que o projeto foi instalado:

```bash
python -m pip show villaz-router
python -m villaz_router --help
```

Em desenvolvimento, reinstale apenas se necessário:

```bash
python -m pip install -e ".[dev]"
```

`python -m villaz_router serve` usa a mesma função principal do comando de console.

## Porta ocupada

Escolha explicitamente outra porta válida:

```bash
villaz-router serve --port 9000
```

Identifique e encerre outro processo somente se ele for conhecido e estiver sob sua responsabilidade.

## Configuração externa incompleta

`--configuration-root` é um override completo. A árvore precisa conter:

```text
config/ollama.yaml
config/router.yaml
profiles/profiles.yaml
rules/domains.yaml
rules/intents.yaml
rules/profiles.yaml
rules/routing.yaml
```

Não há merge nem fallback para os package resources. Confirme o path informado e a consistência dos YAMLs.

Para retornar ao default empacotado, inicie sem `--configuration-root`.

## Startup falha antes de servir requests

O lifespan carrega Ruleset, Profile Registry, compatibilidade e `config/ollama.yaml`. Uma falha nessa sequência impede startup parcial.

Verifique:

- existência e leitura dos arquivos;
- sintaxe YAML;
- referências Router ↔ Registry;
- profiles habilitados;
- configuração do cliente Ollama.

Não masque o erro com uma segunda raiz ou fallback.

## Ollama indisponível

Readiness não faz probe de rede; portanto, `{"status":"ready"}` não garante que o processo Ollama está acessível.

Confirme separadamente, usando ferramentas do próprio Ollama, se:

- o serviço está ativo;
- `http://127.0.0.1:11434` corresponde à configuração vigente;
- o acesso loopback está permitido;
- não há outro processo ocupando a porta.

Erros de conexão são apresentados publicamente como `MODEL_SERVICE_UNAVAILABLE` com HTTP 503.

## Modelo ausente

Liste os modelos administrados pelo Ollama:

```bash
ollama list
```

Compare os identificadores com `profiles/profiles.yaml`. O projeto não baixa modelos automaticamente e não tenta outro modelo como fallback.

## Host `0.0.0.0` e exposição

O default é `127.0.0.1`. Bind não-loopback é opt-in e gera warning porque a API não possui autenticação como mecanismo de proteção neste estágio.

Se a exposição não foi intencional, reinicie sem `--host`. Se foi intencional, controle a rede fora do processo e não exponha prompts ou respostas em logs.

## Git não reconhece o diretório

Não use `git init` como correção automática. Primeiro confirme que o shell está no clone correto:

```bash
git rev-parse --show-toplevel
git status
```

Se o comando falhar, localize o diretório realmente clonado ou obtenha novamente o código em outro local. Não recrie metadados Git sobre uma árvore existente sem entender sua origem.

## Working tree inesperadamente alterado

Inspecione sem descartar dados:

```bash
git status --short
git diff
git diff --check
```

Não use reset, checkout ou restore até identificar a propriedade e a finalidade de cada alteração.
