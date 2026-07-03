# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Stack

- Python 3.12
- Flask 3.1 + Flask-CORS
- SQLite (`loja.db`, criado automaticamente no primeiro boot)
- Autenticação via token assinado (`itsdangerous`), enviado no header `Authorization: Bearer <token>`

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Como rodar

```bash
python app.py
```

A aplicação sobe em `http://localhost:5000`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot e populado com 10 produtos e 3 usuários de exemplo, caso a tabela de produtos esteja vazia.

Variáveis de ambiente aceitas (todas opcionais, com valores padrão de desenvolvimento):

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | `dev-only-key-change-me` | Chave usada para assinar os tokens de autenticação |
| `DB_PATH` | `loja.db` | Caminho do arquivo SQLite |
| `FLASK_DEBUG` | `false` | Ativa o modo debug do Flask quando `true` |
| `HOST` | `0.0.0.0` | Host de bind |
| `PORT` | `5000` | Porta de bind |

### Usuários de exemplo

| E-mail | Senha | Tipo |
|---|---|---|
| admin@loja.com | admin123 | admin |
| joao@email.com | 123456 | cliente |
| maria@email.com | senha123 | cliente |

## Testes

O projeto ainda não possui uma suíte de testes automatizados. A validação abaixo, feita via curl, é a forma atual de conferir se a aplicação está funcionando corretamente.

## Testando as rotas com curl

Todas as respostas seguem o formato `{"dados": ..., "sucesso": true/false, "mensagem": "..."}` em caso de sucesso, e `{"erro": "...", "sucesso": false}` em caso de erro.

### Autenticação

Faça login para obter um token válido por 8 horas:

```bash
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@loja.com",
    "senha": "admin123"
  }'
```

Use o token retornado no header `Authorization: Bearer <token>` nas rotas que exigem autenticação.

### Sistema

```bash
# Informações da API
curl http://localhost:5000/

# Healthcheck
curl http://localhost:5000/health

# Relatório de vendas
curl http://localhost:5000/relatorios/vendas

# Resetar o banco (apenas admin)
curl -X POST http://localhost:5000/admin/reset-db \
  -H "Authorization: Bearer <token_admin>"
```

### Produtos

```bash
# Listar produtos
curl http://localhost:5000/produtos

# Buscar produtos com filtros
curl "http://localhost:5000/produtos/busca?q=notebook&categoria=informatica&preco_min=100&preco_max=6000"

# Buscar produto por id
curl http://localhost:5000/produtos/1

# Criar produto (apenas admin)
curl -X POST http://localhost:5000/produtos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token_admin>" \
  -d '{
    "nome": "Mousepad Gamer",
    "descricao": "Mousepad extra grande",
    "preco": 49.90,
    "estoque": 100,
    "categoria": "informatica"
  }'

# Atualizar produto (apenas admin)
curl -X PUT http://localhost:5000/produtos/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token_admin>" \
  -d '{
    "nome": "Notebook Gamer Pro",
    "descricao": "Notebook potente para jogos - atualizado",
    "preco": 6499.99,
    "estoque": 8,
    "categoria": "informatica"
  }'

# Remover produto - soft delete (apenas admin)
curl -X DELETE http://localhost:5000/produtos/1 \
  -H "Authorization: Bearer <token_admin>"
```

Categorias válidas: `informatica`, `moveis`, `vestuario`, `geral`, `eletronicos`, `livros`.

### Usuários

```bash
# Cadastrar usuário (rota pública)
curl -X POST http://localhost:5000/usuarios \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "Carlos Souza",
    "email": "carlos@email.com",
    "senha": "minhasenha123"
  }'

# Listar usuários (apenas admin)
curl http://localhost:5000/usuarios \
  -H "Authorization: Bearer <token_admin>"

# Buscar usuário por id (dono do recurso ou admin)
curl http://localhost:5000/usuarios/2 \
  -H "Authorization: Bearer <token_do_proprio_usuario_ou_admin>"
```

### Pedidos

```bash
# Criar pedido (usuário autenticado)
curl -X POST http://localhost:5000/pedidos \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "usuario_id": 2,
    "itens": [
      {"produto_id": 1, "quantidade": 1},
      {"produto_id": 2, "quantidade": 2}
    ]
  }'

# Listar todos os pedidos (apenas admin)
curl http://localhost:5000/pedidos \
  -H "Authorization: Bearer <token_admin>"

# Listar pedidos de um usuário (dono do recurso ou admin)
curl http://localhost:5000/pedidos/usuario/2 \
  -H "Authorization: Bearer <token_do_usuario_2_ou_admin>"

# Atualizar status de um pedido (apenas admin)
curl -X PUT http://localhost:5000/pedidos/1/status \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token_admin>" \
  -d '{"status": "aprovado"}'
```

Status válidos: `pendente`, `aprovado`, `enviado`, `entregue`, `cancelado`.

## Observações

- A rota `/relatorios/vendas` expõe dados de faturamento sem exigir autenticação.
- O CORS está habilitado globalmente, sem restrição de origem.
- Não existe `Dockerfile` ou `docker-compose.yml` no projeto.
