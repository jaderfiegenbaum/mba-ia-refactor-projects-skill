================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js / Express 4.18.2 (sqlite3 5.1.6)
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 4 | HIGH: 2 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] God Class / God File concentrando rotas, SQL e regra de negócio
File: src/AppManager.js:1-142
Description: A classe `AppManager` define, no mesmo arquivo, o schema do banco (`initDb`), o roteamento HTTP (`setupRoutes`), o acesso a dados via SQL cru (`this.db.get/run/all`) e a regra de negócio de checkout, matrícula, pagamento e relatório financeiro para múltiplos domínios (usuários, cursos, matrículas, pagamentos, auditoria).
Impact: Qualquer alteração pontual, como mudar a regra de aprovação de pagamento, arrisca quebrar o cadastro de usuário ou o relatório financeiro, pois tudo compartilha o mesmo arquivo e os mesmos callbacks aninhados, sem possibilidade de teste unitário isolado.
Recommendation: Separar em Models por entidade (User, Course, Enrollment, Payment, AuditLog), Controllers por fluxo (CheckoutController, AdminController) e Routes que apenas mapeiam HTTP para os controllers, conforme o padrão de decomposição de God Class do playbook.

### [CRITICAL] Rota destrutiva sem autenticação nem autorização
File: src/AppManager.js:131-137
Description: A rota `DELETE /api/users/:id` apaga qualquer usuário do banco a partir de um id na URL, sem nenhuma checagem de sessão, token ou papel de administrador.
Impact: Qualquer cliente da API, sem se autenticar, pode apagar qualquer usuário do sistema apenas trocando o `:id` na URL.
Recommendation: Adicionar middleware de autenticação/autorização (verificação de token e papel admin) antes do handler, conforme o padrão de middleware de auth do playbook, negando a requisição com 401/403 quando ausente ou inválida.

### [CRITICAL] Credenciais e segredos hardcoded no código fonte
File: src/utils.js:1-6
Description: O objeto `config` grava literalmente no código `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser`, além disso a chave de pagamento é impressa em log (`AppManager.js:45`) em toda chamada de checkout.
Impact: Qualquer pessoa com acesso ao repositório (incluindo histórico de commits) tem acesso imediato à chave de produção do gateway de pagamento e à senha do banco, podendo processar cobranças ou acessar dados de produção diretamente.
Recommendation: Mover todos os segredos para variáveis de ambiente (`process.env.PAYMENT_GATEWAY_KEY`, etc.) carregadas por um módulo de config dedicado, e remover o log da chave em `AppManager.js:45`.

### [CRITICAL] Hashing de senha caseiro baseado em Base64
File: src/utils.js:17-23
Description: A função `badCrypto` concatena repetidamente uma fatia de `Buffer.from(pwd).toString('base64')` 10000 vezes e corta o resultado em 10 caracteres, produzindo um valor totalmente reversível, usado como "hash" de senha em `AppManager.js:68`.
Impact: Qualquer senha armazenada no banco (`users.pass`) pode ser revertida trivialmente a partir do Base64, expondo a senha original de todos os usuários caso o banco vaze, com risco adicional de reuso de senha em outros sistemas.
Recommendation: Substituir `badCrypto` por bcrypt ou argon2 com salt, gerando o hash em `AppManager.js:68` a partir da lib escolhida, conforme o padrão de hashing seguro do playbook.

### [HIGH] Lógica de negócio pesada dentro do handler de rota de checkout
File: src/AppManager.js:28-78
Description: O handler `POST /api/checkout` faz, tudo dentro da própria função de rota: validação de campos obrigatórios, busca de curso, busca/criação de usuário, hashing de senha, decisão de aprovação de pagamento (`cc.startsWith("4")`), matrícula, registro de pagamento e log de auditoria, encadeados em callbacks aninhados.
Impact: A regra de negócio de checkout fica acoplada ao transporte HTTP, tornando impossível testá-la sem subir um servidor Express e simular requisições, e qualquer novo canal de checkout (ex: admin criando matrícula manual) precisaria duplicar toda essa lógica.
Recommendation: Extrair o fluxo para um `CheckoutController`/`CheckoutService` que orquestra chamadas a `UserModel`, `CourseModel`, `EnrollmentModel` e `PaymentModel`, deixando a rota apenas repassar `req.body` e devolver a resposta do controller.

### [HIGH] Ausência de transação atômica no fluxo de pagamento e matrícula
File: src/AppManager.js:50-63
Description: A inserção da matrícula (`INSERT INTO enrollments`), do pagamento (`INSERT INTO payments`) e do log de auditoria (`INSERT INTO audit_logs`) são três escritas encadeadas e independentes, sem transação nem rollback, dentro do fluxo de checkout que envolve dinheiro.
Impact: Se a segunda ou terceira escrita falhar (por exemplo, queda de conexão com o banco), o usuário fica matriculado sem que o pagamento correspondente seja registrado (ou vice-versa), gerando inconsistência financeira sem possibilidade de reversão automática.
Recommendation: Envolver as três escritas em uma transação SQLite (`BEGIN`/`COMMIT`/`ROLLBACK`) dentro do Model responsável pelo checkout, conforme o padrão de transação atômica do playbook.

### [MEDIUM] Query N+1 no relatório financeiro administrativo
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` busca todos os cursos e, para cada curso, faz um novo SELECT de matrículas; para cada matrícula, faz mais dois SELECTs (usuário e pagamento) dentro do `forEach`, resultando em `1 + N + 2*M` queries onde N é o número de cursos e M o total de matrículas.
Impact: O tempo de resposta do relatório cresce proporcionalmente ao volume de cursos e matrículas, tornando o endpoint lento ou até indisponível à medida que a base de dados cresce em produção.
Recommendation: Substituir a cadeia de SELECTs aninhados por uma única query com JOINs entre `courses`, `enrollments`, `users` e `payments`, agregando os dados em memória a partir de um único result set, conforme o padrão de eliminação de N+1 do playbook.

### [MEDIUM] Ausência de validação de entrada no checkout e na exclusão de usuário
File: src/AppManager.js:29-35, 131-133
Description: O checkout só verifica se `usr`, `eml`, `c_id` e `card` são truthy (`if (!u || !e || !cid || !cc)`), sem validar formato de email, formato/tamanho do cartão ou tipo do `c_id`; a rota `DELETE /api/users/:id` usa `req.params.id` direto na query sem validar que é um número.
Impact: Dados inconsistentes podem ser gravados no banco (emails inválidos, ids não numéricos causando comportamento inesperado no driver), e erros de tipo só aparecem em camadas mais profundas, dificultando o diagnóstico.
Recommendation: Adicionar uma camada de validação de entrada (schema de validação por rota) antes de repassar os dados ao Controller/Model, rejeitando com 400 os formatos inválidos.

### [MEDIUM] Exclusão de usuário deixa referências órfãs no banco
File: src/AppManager.js:131-137
Description: O handler de `DELETE /api/users/:id` apaga a linha de `users` e retorna a mensagem "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco", sem apagar ou tratar as linhas relacionadas em `enrollments` e `payments`.
Impact: Consultas futuras que dependem de `enrollments.user_id` ou de relatórios que fazem join com `users` passam a referenciar um id inexistente, retornando dado inconsistente (`Unknown` no relatório financeiro) sem que a causa raiz (a exclusão) fique visível no momento do erro.
Recommendation: Definir uma estratégia explícita no Model (cascade delete, soft-delete via coluna `deleted_at`, ou bloqueio da exclusão quando há matrículas ativas) em vez de deixar o problema documentado em texto na resposta da API.

### [LOW] Dados sensíveis expostos via console.log
File: src/AppManager.js:45; src/utils.js:13
Description: `console.log` imprime o número do cartão de crédito completo e a chave do gateway de pagamento em toda chamada de checkout (`AppManager.js:45`), e `logAndCache` (`utils.js:13`) loga a chave de cache que inclui o id do usuário.
Impact: Em produção, esses logs ficam em stdout/arquivos de log sem controle de nível ou redação, expondo dado sensível de cartão e chave de API para qualquer pessoa com acesso aos logs.
Recommendation: Substituir `console.log` por um logger estruturado (ex: `pino`/`winston`) com redação de campos sensíveis (mascarar cartão, nunca logar chaves de API).

### [LOW] Nomenclatura ruim e magic number no fluxo de checkout
File: src/AppManager.js:29-32; src/utils.js:19
Description: As variáveis do handler de checkout usam nomes de uma ou duas letras sem significado (`u`, `e`, `p`, `cid`, `cc`) para usuário, email, senha, curso e cartão; `badCrypto` usa o literal `10000` como número de iterações sem constante nomeada.
Impact: Obriga quem lê o código a inferir o significado de cada variável pelo contexto de uso, tornando revisões e manutenção mais lentas e propensas a erro.
Recommendation: Renomear para nomes descritivos (`username`, `email`, `password`, `courseId`, `cardNumber`) e extrair `10000` para uma constante nomeada, caso a lógica de hashing seja mantida temporariamente até a substituição por bcrypt/argon2.

### [LOW] Import não utilizado (código morto)
File: src/utils.js:10, 25; src/AppManager.js:2
Description: `totalRevenue` é declarado e exportado em `utils.js` e importado em `AppManager.js:2`, mas nunca é lido, incrementado ou usado em nenhum ponto do código.
Impact: Aumenta a superfície de código para ler sem entregar valor, e pode levar quem lê o projeto a acreditar que existe um acumulador de receita ativo quando, na verdade, ele nunca é atualizado.
Recommendation: Remover `totalRevenue` de `utils.js` e da desestruturação em `AppManager.js:2`, já que o relatório financeiro calcula a receita por curso de forma independente.

================================
Total: 12 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
