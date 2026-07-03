# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Diferente dos outros projetos, este já possui alguma separação de camadas (`models/`, `routes/`, `services/`, `utils/`), mas ainda contém problemas arquiteturais e de qualidade.

## Stack

- Python 3.10+ (testado com 3.12)
- Flask 3.0 + Flask-SQLAlchemy + Flask-CORS
- SQLite (`instance/tasks.db`)
- Autenticação via JWT (`PyJWT`), enviado no header `Authorization: Bearer <token>`

## Instalação

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copie o arquivo de variáveis de ambiente de exemplo antes de rodar a aplicação:

```bash
cp .env.example .env
```

Variáveis disponíveis:

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | `change-me-in-production` | Chave usada para assinar e validar os tokens JWT |
| `DATABASE_URL` | `sqlite:///tasks.db` | URI de conexão do banco |
| `SMTP_HOST` | `smtp.gmail.com` | Servidor usado para notificar usuários por e-mail ao atribuir uma task |
| `SMTP_PORT` | `587` | Porta do servidor SMTP |
| `SMTP_USER` | vazio | Usuário SMTP; se vazio, o envio de e-mail é apenas logado e não quebra a aplicação |
| `SMTP_PASSWORD` | vazio | Senha SMTP |

## Como rodar

```bash
python seed.py
python app.py
```

A aplicação sobe em `http://localhost:5000`. O `seed.py` apaga os dados existentes e popula o banco SQLite com 3 usuários, 4 categorias e 10 tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

### Usuários de exemplo (criados pelo seed)

| E-mail | Senha | Papel |
|---|---|---|
| joao@email.com | 1234 | admin |
| maria@email.com | abcd | user |
| pedro@email.com | pass | manager |

## Testes

O projeto ainda não possui uma suíte de testes automatizados. A validação abaixo, feita via curl, é a forma atual de conferir se a aplicação está funcionando corretamente.

## Testando as rotas com curl

### Autenticação

Faça login para obter um token JWT válido por 8 horas:

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "joao@email.com", "password": "1234"}'
```

Guarde o token retornado numa variável para reutilizar nos exemplos seguintes:

```bash
TOKEN=$(curl -s -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")
```

### Sistema

```bash
curl http://localhost:5000/
curl http://localhost:5000/health
```

### Usuários

```bash
# Cadastro público (sempre cria papel "user")
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "Ana Costa", "email": "ana@email.com", "password": "senha123"}'

# Listar usuários
curl http://localhost:5000/users -H "Authorization: Bearer $TOKEN"

# Buscar usuário por id (com tasks embutidas)
curl http://localhost:5000/users/1 -H "Authorization: Bearer $TOKEN"

# Atualizar usuário
curl -X PUT http://localhost:5000/users/2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Maria S. Santos", "active": true}'

# Promover usuário a admin (exige token de um admin)
curl -X PUT http://localhost:5000/users/2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role": "admin"}'

# Remover usuário (apenas admin)
curl -X DELETE http://localhost:5000/users/3 -H "Authorization: Bearer $TOKEN"

# Listar tasks de um usuário
curl http://localhost:5000/users/1/tasks -H "Authorization: Bearer $TOKEN"
```

### Tasks

```bash
# Listar todas as tasks
curl http://localhost:5000/tasks -H "Authorization: Bearer $TOKEN"

# Buscar tasks com filtros
curl "http://localhost:5000/tasks/search?q=bug&status=pending&priority=1&user_id=1" \
  -H "Authorization: Bearer $TOKEN"

# Estatísticas das tasks
curl http://localhost:5000/tasks/stats -H "Authorization: Bearer $TOKEN"

# Buscar task por id
curl http://localhost:5000/tasks/1 -H "Authorization: Bearer $TOKEN"

# Criar task
curl -X POST http://localhost:5000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Nova task de exemplo",
    "description": "Descrição da task",
    "status": "pending",
    "priority": 2,
    "user_id": 1,
    "category_id": 1,
    "due_date": "2026-08-15",
    "tags": ["backend", "urgente"]
  }'

# Atualizar task
curl -X PUT http://localhost:5000/tasks/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "done", "priority": 1}'

# Remover task
curl -X DELETE http://localhost:5000/tasks/1 -H "Authorization: Bearer $TOKEN"
```

Campos aceitos ao criar ou atualizar uma task:

| Campo | Tipo | Observações |
|---|---|---|
| `title` | string | obrigatório na criação, 3 a 200 caracteres |
| `description` | string | opcional |
| `status` | string | `pending`, `in_progress`, `done` ou `cancelled` (padrão `pending`) |
| `priority` | number | de 1 a 5 (padrão 3) |
| `user_id` | number | precisa existir; dispara notificação ao atribuir |
| `category_id` | number | precisa existir |
| `due_date` | string | formato `YYYY-MM-DD` ou `DD/MM/YYYY` |
| `tags` | array ou string | lista de tags, aceita também string separada por vírgula |

### Categorias

```bash
# Listar categorias
curl http://localhost:5000/categories -H "Authorization: Bearer $TOKEN"

# Criar categoria
curl -X POST http://localhost:5000/categories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "QA", "description": "Tarefas de qualidade", "color": "#9b59b6"}'

# Atualizar categoria
curl -X PUT http://localhost:5000/categories/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"color": "#1abc9c"}'

# Remover categoria (desassocia as tasks vinculadas, sem apagá-las)
curl -X DELETE http://localhost:5000/categories/1 -H "Authorization: Bearer $TOKEN"
```

### Relatórios

```bash
# Resumo geral (totais por status, prioridade, atrasos e produtividade por usuário)
curl http://localhost:5000/reports/summary -H "Authorization: Bearer $TOKEN"

# Relatório de um usuário específico
curl http://localhost:5000/reports/user/1 -H "Authorization: Bearer $TOKEN"
```

## Observações

- Todas as rotas de tasks, categorias e relatórios exigem autenticação; apenas `/`, `/health`, `/login` e o cadastro em `POST /users` são públicas.
- A alteração de papel (`role`) de um usuário só é permitida para quem já está autenticado como admin.
- O banco `instance/tasks.db` já existe versionado no repositório.
