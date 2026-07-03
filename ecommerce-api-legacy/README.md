# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Stack

- Node.js 18+
- Express 4
- SQLite em memória (`sqlite3`), recriado do zero a cada boot
- bcryptjs para hash de senha

## Instalação

```bash
npm install
```

## Como rodar

```bash
npm start
```

A aplicação sobe em `http://localhost:3000` (equivalente a `node src/app.js`). O banco SQLite é em memória e recriado a cada boot, já populado com os seguintes dados:

- Usuário: `Leonan` (leonan@fullcycle.com.br, senha `123`)
- Cursos: `Clean Architecture` (R$ 997,00) e `Docker` (R$ 497,00)
- Uma matrícula existente do Leonan no curso Clean Architecture, com pagamento já aprovado

Variáveis de ambiente aceitas (todas opcionais, com valores padrão de desenvolvimento):

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `3000` | Porta HTTP do Express |
| `ADMIN_API_KEY` | `dev-only-admin-key-change-me` | Chave exigida no header `x-admin-key` para deletar usuários |
| `DB_PASS` | `dev-only-password-change-me` | Declarada mas não utilizada (o banco é em memória) |
| `PAYMENT_GATEWAY_KEY` | `dev-only-key-change-me` | Declarada mas não utilizada (o gateway de pagamento é simulado) |
| `SMTP_USER` | `no-reply@example.com` | Declarada mas não utilizada (não há envio de e-mail implementado) |

## Testes

O projeto ainda não possui uma suíte de testes automatizados. A validação abaixo, feita via curl, é a forma atual de conferir se a aplicação está funcionando corretamente. Exemplos adicionais também estão disponíveis em `api.http`.

## Testando as rotas com curl

### POST /api/checkout

Cria um usuário (se ainda não existir), simula a cobrança no cartão e matricula o aluno no curso. O pagamento é aprovado apenas se o número do cartão começar com o dígito `4`; qualquer outro dígito inicial é recusado.

```bash
# Checkout com sucesso (cartão começa com 4 → aprovado)
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "usr": "Guilherme",
    "eml": "gui@fullcycle.com.br",
    "pwd": "senhaforte",
    "c_id": 2,
    "card": "4111222233334444"
  }'

# Checkout com pagamento recusado (cartão não começa com 4)
curl -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{
    "usr": "João",
    "eml": "joao@teste.com",
    "pwd": "123",
    "c_id": 1,
    "card": "5111222233334444"
  }'
```

Campos do body:

| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `usr` | string | sim | Nome do usuário |
| `eml` | string | sim | E-mail do usuário |
| `pwd` | string | não | Senha; se omitida, usa `123456` como padrão (só é aplicada se o usuário ainda não existir) |
| `c_id` | number | sim | Id do curso |
| `card` | string | sim | Número do cartão (13 a 19 dígitos) |

### GET /api/admin/financial-report

Retorna o relatório financeiro agregado por curso, com receita total e alunos matriculados. Não exige autenticação.

```bash
curl http://localhost:3000/api/admin/financial-report
```

### DELETE /api/users/:id

Remove um usuário e todos os dados relacionados (pagamentos e matrículas). Exige o header `x-admin-key`.

```bash
curl -X DELETE http://localhost:3000/api/users/1 \
  -H "x-admin-key: dev-only-admin-key-change-me"
```

## Observações

- A rota `GET /api/admin/financial-report` está sob o prefixo `/admin` mas não exige nenhuma autenticação, apesar de expor dados financeiros.
- Não há rota de login nem autenticação de usuário implementada; o `x-admin-key` é o único mecanismo de proteção existente.
- Não existe `Dockerfile` ou `docker-compose.yml` no projeto.
