# Análise de Projeto

Este arquivo descreve como detectar a stack e mapear a arquitetura atual de qualquer projeto de backend, sem assumir de antemão qual linguagem ou framework está em uso.

## Detecção de linguagem

Olhe primeiro para os arquivos de manifesto de dependências, que quase sempre denunciam a linguagem:

- `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` indicam Python
- `package.json` indica JavaScript ou TypeScript (verifique `tsconfig.json` para diferenciar)
- `go.mod` indica Go
- `pom.xml` ou `build.gradle` indicam Java ou Kotlin
- `Gemfile` indica Ruby
- `composer.json` indica PHP

Se nenhum manifesto existir, use a extensão predominante dos arquivos fonte (`.py`, `.js`, `.ts`, `.go`, `.java`, `.rb`, `.php`) como critério de desempate.

Para a versão da linguagem, procure em `pyproject.toml` (`python_requires`), `package.json` (`engines.node`), `go.mod` (`go 1.x`) ou similar. Se não houver informação explícita, reporte como "não especificada" em vez de adivinhar.

## Detecção de framework

Depois de identificar a linguagem, cruze as dependências declaradas com os frameworks mais comuns:

- Python: `flask`, `django`, `fastapi`, `bottle`
- Node.js: `express`, `koa`, `fastify`, `nestjs`
- Java: `spring-boot`, `spring-web`
- Ruby: `rails`, `sinatra`

Confirme a detecção olhando o código: presença de `Flask(__name__)`, `app = express()`, `@app.route`, `router.get(...)`, decorators de rota, etc. A versão do framework normalmente está no mesmo manifesto de dependências (`flask==3.1.1`, `"express": "^4.18.0"`).

Se o manifesto não fixar versão (ex: `flask` sem pin), reporte a versão instalada no ambiente, se disponível, ou marque como "versão não fixada no manifesto".

## Detecção de banco de dados

Procure por:

- Import de driver ou ORM: `sqlite3`, `psycopg2`, `pymongo`, `sqlalchemy`, `mongoose`, `pg`, `mysql2`, `better-sqlite3`
- String de conexão hardcoded ou em variável de ambiente (`DATABASE_URL`, `DB_PATH`)
- Arquivos `.db`, `.sqlite`, `.sqlite3` no projeto
- Chamadas de schema (`CREATE TABLE`, `db.schema`, migrations)

Liste as tabelas ou coleções encontradas lendo os `CREATE TABLE` (SQL) ou as definições de schema/model (ORM). Se não houver banco de dados algum, reporte "none detected" no resumo da Fase 1, não deixe o campo em branco.

## Mapeamento da arquitetura atual

O objetivo aqui não é apenas contar arquivos, é entender como as responsabilidades estão distribuídas hoje, para saber o tamanho do trabalho de refatoração. Classifique o projeto em um destes perfis, e descreva o motivo em uma frase:

- **Monolítico em poucos arquivos**: toda a lógica (rotas, acesso a dados, regra de negócio) está concentrada em 1 a 4 arquivos na raiz do projeto, sem pastas dedicadas por camada. Sinal típico: um `models.py` ou `AppManager.js` de centenas de linhas fazendo tudo.
- **Parcialmente organizado**: já existem pastas como `models/`, `routes/`, `services/` ou `utils/`, mas as responsabilidades vazam entre elas (por exemplo, regra de negócio duplicada nas rotas mesmo havendo um model pronto, ou serviços que nunca são chamados). Descreva especificamente o que já está bem separado e o que ainda vaza.
- **MVC já aplicado**: as três camadas existem, são usadas de forma consistente e não há vazamento relevante de responsabilidade. Nesse caso a Fase 3 deve ser mínima, focada apenas nos findings pontuais da auditoria.

Para contar "arquivos analisados", conte apenas arquivos de código fonte da aplicação (ignore dependências instaladas, arquivos de configuração de IDE, lockfiles e a própria pasta da skill).

## Detecção de domínio da aplicação

Infira o domínio de negócio olhando para:

- Nomes de rotas e endpoints (`/produtos`, `/pedidos`, `/courses`, `/checkout`, `/tasks`)
- Nomes de tabelas e entidades (`produtos`, `usuarios`, `courses`, `enrollments`, `tasks`, `categories`)
- Comentários e docstrings de topo de arquivo, se existirem

Descreva o domínio em uma frase objetiva, por exemplo "API de E-commerce (produtos, pedidos, usuários)" ou "LMS com fluxo de checkout de cursos" ou "Task Manager com categorias e relatórios". Evite genérico demais como "API REST".
