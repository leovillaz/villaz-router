# Segurança

Segurança e privacidade são requisitos transversais do Villaz Router.

## Princípios

- nenhum LLM participa da decisão do Router;
- rulesets inválidos não entram em operação;
- referências cruzadas são validadas antes do uso;
- o ruleset ativo deve ser imutável durante a instância;
- dados internos de infraestrutura não devem vazar em `RouteDecision`;
- a mensagem integral do usuário não deve ser armazenada automaticamente;
- IDs de perfil dentro da mensagem não possuem autoridade de controle;
- texto como `SYSTEM:`, `PROFILE:` ou `ROUTE:` dentro da mensagem é apenas conteúdo;
- perfil manual inválido não deve cair silenciosamente para roteamento automático.

## Secrets

Não versionar:

- tokens;
- senhas;
- chaves privadas;
- `.env` com credenciais;
- arquivos de configuração local contendo segredos.

O `.gitignore` deve excluir `.env`.

## Relato de vulnerabilidades

Enquanto o repositório for privado, reporte diretamente ao mantenedor.

Antes da abertura pública, recomenda-se habilitar o **Private Vulnerability Reporting** do GitHub e atualizar este documento com o canal oficial.

## Escopo atual

O Router é um componente de decisão. Autenticação, autorização, FastAPI, Ollama e infraestrutura pertencem a outras camadas e devem ter controles próprios.
