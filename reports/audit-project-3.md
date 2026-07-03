================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python / Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   15 analyzed | ~1150 lines of code

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 5 | LOW: 4

## Findings

### [CRITICAL] Credenciais e segredos hardcoded
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` está escrito literalmente no código-fonte em vez de vir de variável de ambiente.
Impact: Qualquer pessoa com acesso ao repositório consegue forjar sessões/assinaturas que dependam dessa chave em produção.
Recommendation: Extrair para `config/settings.py`, lendo de `os.environ.get('SECRET_KEY', ...)` com um valor default apenas para desenvolvimento local, conforme o padrão "Extrair configuração e segredos para variáveis de ambiente".

### [CRITICAL] Credenciais SMTP hardcoded em serviço órfão
File: services/notification_service.py:7-10
Description: `NotificationService.__init__` grava host, porta, usuário e senha SMTP (`self.email_password = 'senha123'`) diretamente no código. O serviço nunca é importado por nenhuma rota ou controller do projeto (`grep` não encontra `NotificationService` fora deste arquivo), ou seja, um segredo real está hardcoded em código morto.
Impact: A credencial de e-mail de produção fica exposta a qualquer leitor do repositório mesmo sem a funcionalidade estar em uso, e pode ser reativada por engano sem que ninguém perceba o risco.
Recommendation: Mover as credenciais para variáveis de ambiente via módulo de config e decidir explicitamente na Fase 3 se o serviço será conectado a um fluxo real (ex.: notificar `notify_task_overdue` quando `Task.is_overdue()`) ou removido — nunca deixá-lo órfão com segredo hardcoded.

### [CRITICAL] Hash de senha e senha exposta na resposta da API
File: models/user.py:16-25, 27-32
Description: `set_password`/`check_password` usam `hashlib.md5` sem salt (linhas 27-32), e `to_dict()` (linhas 16-25) inclui o campo `password` (o hash MD5) na serialização devolvida ao cliente. Esse `to_dict()` é usado em `POST /users` (routes/user_routes.py:86), `GET /users/<id>` (routes/user_routes.py:33), `PUT /users/<id>` (routes/user_routes.py:129) e `POST /login` (routes/user_routes.py:209).
Impact: MD5 é trivialmente quebrado por rainbow table, e como o hash também vaza em toda resposta que serializa um usuário, qualquer cliente da API consegue coletar hashes de senha de todos os usuários e reverter para a senha em texto claro, comprometendo contas que reusam a mesma senha em outros sistemas.
Recommendation: Trocar o hashing por `werkzeug.security.generate_password_hash`/`check_password_hash` (ou bcrypt) e remover o campo `password` de `to_dict()`, conforme os padrões "Trocar hashing fraco de senha" e a regra de nunca serializar o hash de senha.

### [CRITICAL] Ausência de autenticação e autorização em toda a API
File: routes/user_routes.py:185-211 (login), routes/task_routes.py (todas as rotas), routes/user_routes.py (todas as rotas exceto login), routes/report_routes.py (todas as rotas)
Description: `POST /login` gera `'fake-jwt-token-' + str(user.id)` (linha 210) mas esse token nunca é lido nem validado em nenhuma rota do projeto — não existe nenhum decorator, middleware ou checagem de header `Authorization` em `task_routes.py`, `user_routes.py` ou `report_routes.py`. Rotas destrutivas como `DELETE /tasks/<id>` (task_routes.py:225-238) e `DELETE /users/<id>` (user_routes.py:134-151), que também apaga em cascata as tasks do usuário, ficam acessíveis a qualquer chamador sem identidade alguma.
Impact: Qualquer cliente não autenticado pode ler, criar, alterar ou apagar dados de qualquer usuário ou task da aplicação, incluindo apagar contas de outros usuários e todas as suas tasks.
Recommendation: Implementar um token real assinado (JWT com expiração) no login e um middleware `require_auth`/`require_admin` aplicado às rotas sensíveis, conforme o padrão "Adicionar autenticação e autorização às rotas sensíveis".

### [HIGH] Lógica de negócio pesada dentro das Routes, sem camada de Controller
File: routes/task_routes.py:85-154 (create_task), routes/task_routes.py:156-223 (update_task), routes/user_routes.py:42-90 (create_user), routes/user_routes.py:92-132 (update_user)
Description: Os handlers de rota fazem validação de negócio completa (tamanho de título, faixa de prioridade, status permitido, formato de e-mail, força de senha), acesso direto ao ORM e formatação da resposta, tudo na mesma função, sem delegar a um Controller. O projeto não possui nenhuma pasta `controllers/`.
Impact: A regra de negócio fica acoplada ao transporte HTTP — não é possível testar "criar task" ou "criar usuário" sem subir o Flask e simular uma requisição, e qualquer mudança de regra exige editar o arquivo de rota inteiro.
Recommendation: Criar `controllers/task_controller.py`, `controllers/user_controller.py` e `controllers/report_controller.py` que recebam os dados já parseados da Route, orquestrem a chamada aos Models e devolvam o resultado formatado, conforme o padrão "Quebrar em Model, Controller e Route por domínio".

### [HIGH] Validação de negócio duplicada em vez de reaproveitar utilitário existente
File: routes/task_routes.py:96-124, routes/task_routes.py:166-213, utils/helpers.py:57-108
Description: `utils/helpers.py` já define `process_task_data(data, existing_task=None)` (linhas 57-108), com toda a validação de título, status, prioridade, data e tags centralizada, mas essa função nunca é importada por `task_routes.py` — as rotas `create_task` e `update_task` reimplementam a mesma validação inline, de forma ligeiramente divergente (por exemplo, `update_task` não usa `parse_date`, que aceita dois formatos de data, e sim `strptime` fixo em `%Y-%m-%d`).
Impact: A regra de validação de task já diverge entre `create_task` e `update_task` (formatos de data aceitos são diferentes), e qualquer correção futura de regra precisa ser replicada manualmente em cada rota, sob risco de esquecer uma.
Recommendation: Fazer `create_task`/`update_task` chamarem `process_task_data` (movido para o futuro Model/Controller de task) em vez de reimplementar a validação, conforme "Remover duplicação de regra de negócio reutilizando o Model existente".

### [HIGH] Duplicação da regra "task atrasada" em 5 lugares diferentes
File: models/task.py:50-60, routes/task_routes.py:30-39, routes/task_routes.py:71-80, routes/task_routes.py:283-287, routes/user_routes.py:171-180, routes/report_routes.py:33-43, routes/report_routes.py:132-135
Description: `Task.is_overdue()` já existe em `models/task.py:50-60` implementando a regra "atrasada = `due_date` no passado e `status` não é `done`/`cancelled`", mas nenhuma rota a chama — cada endpoint (`get_tasks`, `get_task`, `task_stats` em task_routes.py; `get_user_tasks` em user_routes.py; `summary_report`, `user_report` em report_routes.py) reimplementa a mesma condição `if/else` aninhada manualmente.
Impact: Mudar a definição de "atrasada" (por exemplo, incluir uma tolerância de horas) exige encontrar e editar 6 blocos de código espalhados em 3 arquivos, com alto risco de deixar algum endpoint com a regra antiga.
Recommendation: Substituir cada bloco condicional por uma chamada a `task.is_overdue()`, conforme "Remover duplicação de regra de negócio reutilizando o Model existente".

### [MEDIUM] Query N+1 ao listar tasks
File: routes/task_routes.py:14-59
Description: `get_tasks()` itera sobre todas as tasks e, para cada uma que tem `user_id`/`category_id`, executa `User.query.get(t.user_id)` (linha 42) e `Category.query.get(t.category_id)` (linha 51) individualmente dentro do loop.
Impact: O número de queries cresce linearmente com o número de tasks (até `1 + 2N`), degradando a performance do endpoint mais usado da API à medida que a base cresce.
Recommendation: Usar `joinedload`/`select_related`-equivalente do SQLAlchemy (`db.session.query(Task).options(joinedload(Task.user), joinedload(Task.category))`) para resolver em uma única consulta, conforme "Resolver Query N+1 com JOIN".

### [MEDIUM] Query N+1 no relatório de produtividade por usuário
File: routes/report_routes.py:53-68
Description: `summary_report()` itera sobre todos os usuários e, para cada um, executa `Task.query.filter_by(user_id=u.id).all()` (linha 56) dentro do loop, em vez de agregar com uma única query.
Impact: Em uma base com muitos usuários, o endpoint `/reports/summary` executa uma query adicional por usuário só para montar `user_productivity`, tornando o relatório cada vez mais lento.
Recommendation: Substituir por uma agregação única (`GROUP BY user_id` com `func.count`/`func.sum` no SQLAlchemy), conforme "Resolver Query N+1 com JOIN".

### [MEDIUM] Query N+1 ao listar categorias com contagem de tasks
File: routes/report_routes.py:157-165
Description: `get_categories()` itera sobre as categorias e executa `Task.query.filter_by(category_id=c.id).count()` (linha 163) uma vez por categoria.
Impact: O endpoint `/categories` faz `1 + N` queries em vez de uma única consulta agregada, com custo crescente conforme o número de categorias aumenta.
Recommendation: Substituir por uma única query com `GROUP BY category_id`, conforme "Resolver Query N+1 com JOIN".

### [MEDIUM] Uso de API deprecated `datetime.utcnow()`
File: models/task.py:15-16,52; models/category.py:11; models/user.py:14; routes/task_routes.py:31,72,136,203,215,285; routes/report_routes.py:35,42,45,48,50-51,71,133; routes/user_routes.py:172; services/notification_service.py:35; utils/helpers.py:38; seed.py:66-75
Description: `datetime.utcnow()` é chamado em praticamente todos os módulos que lidam com datas, tanto para default de coluna (`db.Column(..., default=datetime.utcnow)`) quanto para comparação de "atrasada".
Impact: `datetime.utcnow()` está deprecated desde Python 3.12 e devolve um datetime *naive* (sem timezone), o que já hoje é uma fonte silenciosa de bugs ao comparar com datas que tenham timezone.
Recommendation: Trocar por `datetime.now(timezone.utc)` em todos os pontos, conforme "Trocar API deprecated pelo equivalente moderno", ajustando as colunas para `DateTime(timezone=True)` se necessário.

### [MEDIUM] Tratamento de erro genérico com `except:` nu
File: routes/task_routes.py:62, routes/task_routes.py:137, routes/task_routes.py:236; routes/user_routes.py:130, routes/user_routes.py:149; routes/report_routes.py:186, routes/report_routes.py:207, routes/report_routes.py:221; utils/helpers.py:46,49
Description: Vários blocos usam `except:` (ou `except Exception` sem log estruturado) para engolir qualquer erro e devolver uma mensagem genérica (`'Erro interno'`, `'Erro ao deletar'`), sem diferenciar o tipo de falha nem registrar detalhe algum.
Impact: Um erro de programação real (bug) e um erro esperado (ex.: violação de constraint do banco) ficam indistinguíveis nos logs, dificultando diagnosticar problemas em produção.
Recommendation: Substituir por um error handler centralizado (`@app.errorhandler`) que capture exceções específicas e logue a exceção original, conforme "Centralizar tratamento de erros".

### [LOW] Uso de `print()` como logging
File: routes/task_routes.py:149,153,219,234; routes/user_routes.py:83,89,147; utils/helpers.py:36-41 (`log_action`, não utilizada)
Description: Eventos de negócio (task criada/atualizada/deletada, usuário criado, erros) são registrados com `print()` em vez de um logger estruturado.
Impact: Não há níveis de severidade nem destino configurável (arquivo, agregador de logs), e em produção essas mensagens se perdem misturadas no stdout do processo.
Recommendation: Substituir por `logging.getLogger(__name__)` configurado em um módulo central, conforme "Substituir print/console.log por logging estruturado".

### [LOW] Imports não utilizados
File: app.py:7 (`os, sys, json`); routes/task_routes.py:7 (`json, os, sys, time`); routes/user_routes.py:6 (`hashlib, json`); utils/helpers.py:3-4,6-7 (`os, sys, math, hashlib`)
Description: Esses módulos são importados mas nunca referenciados no corpo dos respectivos arquivos (confirmado por busca textual em cada arquivo).
Impact: Aumenta o ruído de leitura do arquivo e pode sugerir, incorretamente, que uma dependência daquele módulo está em uso.
Recommendation: Remover as importações não utilizadas, conforme "Remover código morto e imports não utilizados".

### [LOW] Utilitários e constantes definidos em `utils/helpers.py` nunca usados
File: utils/helpers.py:19-56, 110-116
Description: `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color`, e as constantes `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY`, `DEFAULT_COLOR` são definidos mas nenhuma rota ou model os importa — as rotas reimplementam a mesma validação com regex e listas literais inline (ex.: `routes/user_routes.py:61`, `routes/task_routes.py:110`).
Impact: Aumenta a superfície de código para ler e manter sem entregar valor, e um leitor pode assumir que essas constantes são a fonte da verdade quando na prática não são usadas em lugar nenhum.
Recommendation: Reaproveitar essas constantes e funções nas rotas/controllers correspondentes (eliminando a duplicação já listada nos findings HIGH acima) ou remover as que de fato não tiverem uso planejado.

### [LOW] Integridade referencial não tratada ao deletar categoria
File: routes/report_routes.py:211-223
Description: `delete_category()` remove a categoria do banco sem antes desvincular ou reatribuir as tasks que apontam para ela via `category_id`, diferente de `delete_user()` (user_routes.py:134-151), que explicitamente apaga as tasks do usuário antes de apagar o usuário.
Impact: Tasks continuam referenciando um `category_id` que não existe mais; `GET /tasks` tentará buscar `Category.query.get(t.category_id)` e obterá `None`, mascarando o problema em vez de sinalizar a inconsistência, e o dado órfão persiste indefinidamente no banco.
Recommendation: Ao deletar uma categoria, definir `category_id = None` nas tasks associadas (ou impedir a exclusão se houver tasks vinculadas), tratando a integridade referencial explicitamente.

================================
Total: 16 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
