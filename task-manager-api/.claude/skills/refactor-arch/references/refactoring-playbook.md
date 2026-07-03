# Playbook de Refatoração

Cada padrão abaixo corresponde a um ou mais anti patterns do catálogo e mostra a transformação concreta a aplicar. Os exemplos trazem a mesma transformação em Python e em JavaScript/Node.js, para deixar claro que o padrão não é preso a uma linguagem. Se o projeto auditado estiver em outra stack (Java, Ruby, Go, PHP), aplique o mesmo princípio adaptando à sintaxe e às convenções idiomáticas dessa linguagem; o que importa é o resultado estrutural (segredo fora do código, query parametrizada, camadas separadas), não a sintaxe do exemplo.

## 1. Extrair configuração e segredos para variáveis de ambiente

Corresponde ao anti pattern "Credenciais e segredos hardcoded".

Antes:
```python
# app.py
SECRET_KEY = "minha-chave-super-secreta-123"
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
```

Depois:
```python
# config/settings.py
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-key-change-me")
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
```
```python
# app.py
from config.settings import SECRET_KEY
app.config["SECRET_KEY"] = SECRET_KEY
```

Nunca devolva `SECRET_KEY` ou qualquer segredo em uma resposta HTTP, mesmo em endpoints de diagnóstico como `/health`.

Em Node.js, o mesmo padrão:

Antes:
```javascript
// utils.js
const dbPass = "senha123";
const paymentGatewayKey = "pk_live_abc123";
module.exports = { dbPass, paymentGatewayKey };
```

Depois:
```javascript
// config/index.js
require("dotenv").config();

module.exports = {
  dbPass: process.env.DB_PASS,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY,
};
```

## 2. Substituir SQL concatenado por queries parametrizadas

Corresponde ao anti pattern "SQL Injection".

Antes:
```python
def buscar_usuario(email):
    query = f"SELECT * FROM usuarios WHERE email = '{email}'"
    return cursor.execute(query).fetchone()
```

Depois:
```python
def buscar_usuario(email):
    query = "SELECT * FROM usuarios WHERE email = ?"
    return cursor.execute(query, (email,)).fetchone()
```

Em ORMs, prefira o construtor de query do próprio ORM (`User.query.filter_by(email=email)`) em vez de montar SQL manualmente.

Em Node.js, o mesmo padrão:

Antes:
```javascript
function buscarUsuario(email) {
  const query = `SELECT * FROM usuarios WHERE email = '${email}'`;
  return db.get(query);
}
```

Depois:
```javascript
function buscarUsuario(email) {
  const query = "SELECT * FROM usuarios WHERE email = ?";
  return db.get(query, [email]);
}
```

## 3. Quebrar God File em Model, Controller e Route por domínio

Corresponde aos anti patterns "God Class/God File" e "Lógica de negócio pesada no Controller/Route".

Antes: um único `models.py` de 300+ linhas com funções de produtos, usuários e pedidos, todas com SQL cru embutido, chamadas direto pelas rotas em `app.py`. Ou, em Node.js, uma única classe `AppManager.js` concentrando schema do banco, rotas Express e regra de negócio de checkout.

Depois (Python/Flask):
```
models/
├── produto_model.py     # só acesso a dados de produto
├── usuario_model.py      # só acesso a dados de usuário
└── pedido_model.py       # só acesso a dados de pedido

controllers/
├── produto_controller.py # orquestra criação/listagem de produto
├── usuario_controller.py
└── pedido_controller.py

routes/
└── routes.py              # declara os endpoints e delega ao controller certo
```

Depois (Node.js/Express), a mesma ideia com a convenção idiomática de pastas do ecossistema:
```
src/
├── models/
│   ├── courseModel.js       # só acesso a dados de curso
│   ├── userModel.js          # só acesso a dados de usuário
│   └── enrollmentModel.js    # só acesso a dados de matrícula/checkout
├── controllers/
│   ├── courseController.js
│   ├── userController.js
│   └── checkoutController.js  # orquestra o fluxo de checkout, chamando os models
└── routes/
    └── index.js                # declara os endpoints e delega ao controller certo
```

Cada Model exporta funções específicas do seu domínio (`ProdutoModel.buscar_por_id` / `courseModel.findById`); cada Controller importa apenas o(s) Model(s) que precisa, e a classe God original deixa de existir como um único ponto concentrando tudo.

## 4. Adicionar autenticação e autorização às rotas sensíveis

Corresponde ao anti pattern "Ausência de autenticação e autorização".

Antes:
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_db():
    database.reset()
    return {"status": "ok"}
```

Depois:
```python
# middlewares/auth.py
from functools import wraps
from flask import request, abort

def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        user = auth_service.validar_token(token)
        if not user or not user.is_admin():
            abort(403)
        return fn(*args, **kwargs)
    return wrapper
```
```python
@app.route("/admin/reset-db", methods=["POST"])
@require_admin
def reset_db():
    return admin_controller.reset_db()
```

Se o projeto já tiver um mecanismo de token (mesmo que falso, como no `task-manager-api`), a prioridade é primeiro trocá-lo por um token real assinado (JWT com expiração, ou sessão de servidor), e só depois conectar a checagem nas rotas.

Em Node.js/Express, o mesmo padrão:

Antes:
```javascript
app.delete("/api/users/:id", (req, res) => {
  db.deleteUser(req.params.id);
  res.json({ status: "ok" });
});
```

Depois:
```javascript
// middlewares/requireAdmin.js
function requireAdmin(req, res, next) {
  const user = authService.validateToken(req.headers.authorization);
  if (!user || !user.isAdmin) return res.status(403).json({ error: "forbidden" });
  req.user = user;
  next();
}
```
```javascript
app.delete("/api/users/:id", requireAdmin, userController.deleteUser);
```

## 5. Trocar hashing fraco de senha por um algoritmo apropriado

Corresponde ao anti pattern "Hashing ou criptografia fraca de senha".

Antes:
```python
import hashlib

def hash_senha(senha):
    return hashlib.md5(senha.encode()).hexdigest()
```

Depois:
```python
from werkzeug.security import generate_password_hash, check_password_hash

def hash_senha(senha):
    return generate_password_hash(senha)

def verificar_senha(hash_armazenado, senha):
    return check_password_hash(hash_armazenado, senha)
```

Em Node.js, o mesmo padrão:

Antes:
```javascript
function badCrypto(senha) {
  return Buffer.from(senha).toString("base64").slice(0, 10);
}
```

Depois:
```javascript
const bcrypt = require("bcrypt");

async function hashSenha(senha) {
  return bcrypt.hash(senha, 12);
}

async function verificarSenha(senha, hash) {
  return bcrypt.compare(senha, hash);
}
```

Garanta também que o hash da senha nunca apareça em `to_dict()`/`toJSON()`/qualquer serialização enviada ao cliente, em nenhuma das duas linguagens.

## 6. Resolver Query N+1 com JOIN

Corresponde ao anti pattern "Query N+1".

Antes:
```python
def get_pedidos_usuario(usuario_id):
    pedidos = cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)).fetchall()
    for pedido in pedidos:
        itens = cursor.execute("SELECT * FROM itens_pedido WHERE pedido_id = ?", (pedido["id"],)).fetchall()
        for item in itens:
            produto = cursor.execute("SELECT nome FROM produtos WHERE id = ?", (item["produto_id"],)).fetchone()
            item["produto_nome"] = produto["nome"]
        pedido["itens"] = itens
    return pedidos
```

Depois:
```python
def get_pedidos_usuario(usuario_id):
    query = """
        SELECT p.id AS pedido_id, i.id AS item_id, i.quantidade, pr.nome AS produto_nome
        FROM pedidos p
        JOIN itens_pedido i ON i.pedido_id = p.id
        JOIN produtos pr ON pr.id = i.produto_id
        WHERE p.usuario_id = ?
    """
    rows = cursor.execute(query, (usuario_id,)).fetchall()
    return agrupar_por_pedido(rows)
```

Em ORMs, o equivalente é usar eager loading (`joinedload`, `select_related`, `.populate()`) em vez de acessar o relacionamento dentro de um loop.

Em Node.js, o mesmo padrão:

Antes:
```javascript
db.all("SELECT * FROM courses", (err, courses) => {
  courses.forEach((course) => {
    db.all("SELECT * FROM enrollments WHERE course_id = ?", [course.id], (err, enrollments) => {
      enrollments.forEach((enr) => {
        db.get("SELECT * FROM users WHERE id = ?", [enr.user_id], (err, user) => { /* ... */ });
        db.get("SELECT * FROM payments WHERE enrollment_id = ?", [enr.id], (err, payment) => { /* ... */ });
      });
    });
  });
});
```

Depois:
```javascript
const query = `
  SELECT c.id AS course_id, e.id AS enrollment_id, u.name AS user_name, p.amount
  FROM courses c
  JOIN enrollments e ON e.course_id = c.id
  JOIN users u ON u.id = e.user_id
  JOIN payments p ON p.enrollment_id = e.id
`;
db.all(query, (err, rows) => agruparPorCurso(rows));
```

## 7. Envolver operações relacionadas em uma transação atômica

Corresponde ao anti pattern "Falta de transação atômica em fluxo crítico".

Antes:
```python
def criar_pedido(usuario_id, itens):
    for item in itens:
        estoque = cursor.execute("SELECT quantidade FROM produtos WHERE id = ?", (item["produto_id"],)).fetchone()
        nova_quantidade = estoque["quantidade"] - item["quantidade"]
        cursor.execute("UPDATE produtos SET quantidade = ? WHERE id = ?", (nova_quantidade, item["produto_id"]))
    conn.commit()
```

Depois:
```python
def criar_pedido(usuario_id, itens):
    with conn:  # abre transação, faz rollback automático em caso de exceção
        for item in itens:
            atualizado = conn.execute(
                "UPDATE produtos SET quantidade = quantidade - ? WHERE id = ? AND quantidade >= ?",
                (item["quantidade"], item["produto_id"], item["quantidade"]),
            )
            if atualizado.rowcount == 0:
                raise EstoqueInsuficiente(item["produto_id"])
```

A checagem e a escrita acontecem na mesma instrução (`quantidade >= ?` na cláusula `WHERE`), eliminando a janela de race condition entre ler o estoque e escrever o novo valor.

## 8. Trocar API deprecated pelo equivalente moderno

Corresponde ao anti pattern "Uso de API ou função deprecated".

Antes:
```python
from datetime import datetime
criado_em = datetime.utcnow()
```

Depois:
```python
from datetime import datetime, timezone
criado_em = datetime.now(timezone.utc)
```

Antes (Node.js/Express):
```javascript
const bodyParser = require("body-parser");
app.use(bodyParser.json());
```

Depois:
```javascript
app.use(express.json());
```

Sempre identifique a API deprecated pelo nome exato e cite o substituto recomendado pela própria documentação oficial da linguagem ou framework, não apenas "trocar por algo mais novo".

## 9. Centralizar tratamento de erros

Corresponde ao anti pattern "Tratamento de erro genérico ou ausente".

Antes:
```python
@app.route("/tasks/<id>")
def get_task(id):
    try:
        return task_controller.buscar(id)
    except:
        return {"error": "algo deu errado"}, 500
```

Depois:
```python
# middlewares/error_handler.py
@app.errorhandler(TaskNotFound)
def handle_not_found(e):
    return {"error": str(e)}, 404

@app.errorhandler(Exception)
def handle_unexpected(e):
    logger.exception("erro não tratado")
    return {"error": "internal server error"}, 500
```
```python
@app.route("/tasks/<id>")
def get_task(id):
    return task_controller.buscar(id)
```

O Controller lança exceções de domínio específicas (`TaskNotFound`) em vez de capturar tudo genericamente; o error handler central decide o status code e o formato da resposta.

Em Node.js/Express, o mesmo padrão:

Antes:
```javascript
app.get("/tasks/:id", (req, res) => {
  try {
    const task = taskController.buscar(req.params.id);
    res.json(task);
  } catch (e) {
    res.status(500).json({ error: "algo deu errado" });
  }
});
```

Depois:
```javascript
// middlewares/errorHandler.js
function errorHandler(err, req, res, next) {
  if (err instanceof TaskNotFoundError) {
    return res.status(404).json({ error: err.message });
  }
  logger.error(err);
  res.status(500).json({ error: "internal server error" });
}
```
```javascript
app.get("/tasks/:id", (req, res, next) => {
  taskController.buscar(req.params.id).then((task) => res.json(task)).catch(next);
});
app.use(errorHandler);
```

## 10. Substituir print/console.log por logging estruturado

Corresponde ao anti pattern "Uso de print como logging".

Antes:
```python
print(f"Usuário {email} fez login")
```

Depois:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("login realizado", extra={"user_email": email})
```

Nunca logue senha, hash de senha, número de cartão ou token de autenticação, mesmo em nível debug.

Em Node.js, o mesmo padrão:

Antes:
```javascript
console.log(`Cobrando cartão ${cc} com a chave ${paymentGatewayKey}`);
```

Depois:
```javascript
const logger = require("./config/logger"); // winston ou pino configurado

logger.info("cobranca_iniciada", { enrollmentId: enr.id });
```

## 11. Centralizar constantes e eliminar magic numbers/strings

Corresponde ao anti pattern "Magic numbers, magic strings e nomenclatura ruim".

Antes:
```python
if categoria not in ["eletronicos", "roupas", "livros", "casa", "esportes"]:
    return {"error": "categoria inválida"}, 400
```

Depois:
```python
# models/produto_model.py
CATEGORIAS_VALIDAS = {"eletronicos", "roupas", "livros", "casa", "esportes"}
```
```python
from models.produto_model import CATEGORIAS_VALIDAS

if categoria not in CATEGORIAS_VALIDAS:
    return {"error": "categoria inválida"}, 400
```

A constante fica definida em um único lugar (perto do Model a que pertence) e é importada por quem precisar, em vez de repetida como literal em cada arquivo.

Em Node.js, o mesmo padrão:

Antes:
```javascript
if (status !== "PAID" && status !== "DENIED" && status !== "PENDING") {
  return res.status(400).json({ error: "status inválido" });
}
```

Depois:
```javascript
// models/paymentStatus.js
const PAYMENT_STATUSES = Object.freeze({ PAID: "PAID", DENIED: "DENIED", PENDING: "PENDING" });
module.exports = { PAYMENT_STATUSES };
```
```javascript
const { PAYMENT_STATUSES } = require("../models/paymentStatus");

if (!Object.values(PAYMENT_STATUSES).includes(status)) {
  return res.status(400).json({ error: "status inválido" });
}
```

## 12. Remover duplicação de regra de negócio reutilizando o Model existente

Corresponde ao anti pattern "Duplicação de lógica de negócio".

Antes:
```python
# repetido em task_routes.py, user_routes.py e report_routes.py
atrasada = task.due_date < datetime.now() and task.status != "done"
```

Depois:
```python
# models/task.py
class Task:
    def is_overdue(self):
        return self.due_date < datetime.now() and self.status != "done"
```
```python
atrasada = task.is_overdue()
```

Antes de criar um método novo, verifique se já existe um método equivalente no Model sem uso (como `Task.is_overdue()` órfão) e reaproveite-o em vez de duplicar a lógica de novo.

Em Node.js, o mesmo padrão:

Antes:
```javascript
// repetido em courseController.js e enrollmentController.js
const aprovado = cc.startsWith("4");
```

Depois:
```javascript
// models/paymentModel.js
function isCartaoAprovado(cc) {
  return cc.startsWith("4");
}
module.exports = { isCartaoAprovado };
```
```javascript
const { isCartaoAprovado } = require("../models/paymentModel");
const aprovado = isCartaoAprovado(cc);
```

## 13. Remover código morto e imports não utilizados

Corresponde ao anti pattern "Código morto e imports não utilizados".

Antes:
```python
import sys, json, os, time  # nenhum destes é usado no arquivo
```

Depois: remova a linha inteira, ou mantenha apenas os imports de fato usados no arquivo.

Em Node.js, o mesmo padrão:

Antes:
```javascript
const fs = require("fs"); // nunca usado no arquivo
const path = require("path"); // nunca usado no arquivo
```

Depois: remova as linhas, ou mantenha apenas os requires de fato usados.

Para um serviço órfão (implementado mas nunca chamado), decida entre duas ações e documente a escolha no relatório da Fase 3: conectar o serviço a um fluxo real que precise dele, ou removê-lo se não houver uso planejado. Nunca deixe um serviço com credenciais hardcoded órfão no projeto sem tratar, mesmo que a decisão seja removê-lo.
