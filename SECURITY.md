# Segurança

Segurança e privacidade são requisitos transversais do Villaz Router.

## Princípios

- nenhum LLM participa da decisão determinística do Router;
- rulesets inválidos não entram em operação;
- referências cruzadas são validadas antes do uso;
- o ruleset ativo permanece imutável durante a instância;
- dados internos de infraestrutura não devem vazar nas respostas públicas;
- a mensagem integral do usuário não deve ser armazenada automaticamente;
- IDs de perfil dentro da mensagem não possuem autoridade de controle;
- texto como `SYSTEM:`, `PROFILE:` ou `ROUTE:` dentro da mensagem é apenas conteúdo;
- perfil manual inválido não deve cair silenciosamente para roteamento automático;
- falhas internas e do serviço de modelos devem usar respostas públicas seguras.

## Relato de vulnerabilidades

Use o **GitHub Private Vulnerability Reporting** como canal oficial para relatar vulnerabilidades. Não publique vulnerabilidades em GitHub Issues públicos.

Antes da abertura pública do repositório, o GitHub Private Vulnerability Reporting deve estar efetivamente habilitado e validado.

O tratamento é realizado em regime de best effort, considerando a severidade e o impacto reportados. Não há SLA formal neste estágio.

Inclua somente as informações necessárias para análise:

- versão ou commit afetado;
- descrição do problema;
- passos de reprodução;
- impacto esperado ou observado;
- evidências mínimas necessárias.

Não inclua senhas, tokens, chaves, dados pessoais, prompts privados, payloads desnecessários ou segredos de infraestrutura.

## Escopo

Estão dentro do escopo:

- código do `villaz-router`;
- Router, Dispatcher, Profile Registry e Application Bootstrap;
- API HTTP própria baseada em FastAPI;
- integração própria com Ollama.

Não são defeitos exclusivos deste projeto:

- vulnerabilidades exclusivamente do Ollama upstream;
- vulnerabilidades exclusivamente de dependências;
- problemas exclusivamente de modelos Qwen, Gemma ou outros fornecedores.

Quando o problema estiver na forma como o `villaz-router` integra ou utiliza esses componentes, ele permanece dentro do escopo deste projeto.

## Proteção de dados e segredos

Não versione senhas, tokens, chaves privadas, credenciais, dados pessoais ou arquivos `.env` com informações sensíveis. Não registre prompts, respostas, system prompts ou dados de configuração sensíveis.
