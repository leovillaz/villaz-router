# Guia de replicação

Este guia separa a reprodução hermética do projeto da execução operacional com Ollama. Wheel, sdist e clean install ainda serão validados no gate de artefatos; o fluxo abaixo parte do código-fonte atual.

## 1. Obter o código

```bash
git clone https://github.com/leovillaz/villaz-router
cd villaz-router
```

## 2. Preparar o Python

Requisito declarado: Python 3.13 ou superior. A matriz CI atual cobre somente Python 3.13; compatibilidade com versões posteriores ainda não é validada pela CI.

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

Ative o venv com o comando apropriado para a plataforma antes de continuar.

## 3. Reprodução hermética

Execute a suíte automatizada:

```bash
python -m pytest -q
```

Os testes normais não exigem servidor Ollama, modelos, GPU, socket ou internet. Integrações substituem os boundaries externos e preservam Router, Dispatcher, Registry e requests reais.

O baseline completo corrente, executado no host Linux autoritativo após o hardening local, é `914 passed in 2.59s`, sem failures ou erros de collection e sem skips ou xfails inesperados reportados. O baseline completo anterior ao hardening foi `893 passed in 2.43s`.

## 4. Preparar o Ollama

Instale e inicie o Ollama usando o procedimento suportado pelo fornecedor. O Villaz Router não instala o serviço e não baixa modelos automaticamente.

Os identificadores distintos referenciados atualmente são:

```text
gemma3:12b
qwen2.5-coder:14b
qwen3:14b
```

Obtenha-os antes da validação operacional:

```bash
ollama pull gemma3:12b
ollama pull qwen2.5-coder:14b
ollama pull qwen3:14b
ollama list
```

Os modelos não são distribuídos nem relicenciados pelo projeto. Após os modelos estarem disponíveis, o fluxo local não deve depender de internet.

## 5. Iniciar a API

```bash
villaz-router serve
```

Equivalente:

```bash
python -m villaz_router serve
```

A CLI usa `127.0.0.1:8000` e os package resources por default. No startup:

1. o `RuntimeContext` é construído;
2. `config/ollama.yaml` é carregado;
3. um único `OllamaExecutor` é criado;
4. contexto e executor são mantidos no lifespan;
5. o executor é fechado no shutdown.

A construção e a readiness não fazem probe ao Ollama.

## 6. Verificar o estado HTTP

Liveness:

```bash
curl http://127.0.0.1:8000/health/live
```

Resposta:

```json
{
  "status": "alive"
}
```

Readiness state-based:

```bash
curl http://127.0.0.1:8000/health/ready
```

Resposta pronta:

```json
{
  "status": "ready"
}
```

Esse resultado confirma `RuntimeContext` e `OllamaExecutor` válidos no lifespan, não conectividade com o Ollama.

## 7. Executar um prompt real

```bash
curl -X POST http://127.0.0.1:8000/v1/prompt \
  -H "Content-Type: application/json" \
  -d '{"message":"Meu Rigidbody está se movimentando de forma irregular."}'
```

Formato de sucesso:

```json
{
  "response": "Resposta produzida pelo modelo.",
  "profile": "unity-dev",
  "model": "qwen2.5-coder:14b",
  "state": "routed",
  "route_id": "ROUTE-UNITY-001"
}
```

`response` pode variar. `profile`, `model`, `state` e `route_id` refletem o plano executado. Consulte [API.md](API.md) para os erros e limites.

## 8. Configuração externa opcional

```bash
villaz-router serve --configuration-root /caminho/para/configuracao
```

A raiz é um override integral: não há merge ou fallback. Ela precisa conter os sete YAMLs operacionais descritos no [guia de instalação](INSTALLATION.md).

## 9. Critérios de reprodução

### Hermética

- pacote importável;
- testes automatizados aprovados;
- package resources presentes;
- nenhum acesso Ollama real durante os testes.

### Operacional

- critérios herméticos atendidos;
- Ollama ativo;
- modelos referenciados disponíveis;
- health endpoints respondendo;
- `POST /v1/prompt` retornando sucesso com execução real.

A validação operacional depende do modelo, quantização, contexto, backend e hardware. Não há promessa de desempenho mínimo.

## Gate ainda pendente

Não considere wheel/sdist, clean clone, clean install ou publicação aprovados apenas por concluir este guia. Esses itens pertencem ao publication gate posterior.
