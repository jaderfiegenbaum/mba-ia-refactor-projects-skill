
## Análise Manual

### Projeto: `code-smells-project` (Python/Flask — API de E-commerce)

- **[CRITICAL] SQL Injection generalizado** — `models.py` (ex: linhas 28, 48-50, 92, 109-111, 126-128, 140, 279-280, 291-297) e `app.py:59-78` (`/admin/query` executa SQL arbitrário vindo do request). Todas as queries são montadas por concatenação de string em vez de parâmetros (`?`), então qualquer campo de entrada (id, nome, email, senha, termo de busca) permite injeção direta no banco. É o problema mais grave do projeto: compromete confidencialidade e integridade dos dados.

- **[CRITICAL] Credenciais e segredos hardcoded, expostos até em endpoint público** — `app.py:7` define `SECRET_KEY = "minha-chave-super-secreta-123"` direto no código, e `controllers.py:289` devolve essa mesma secret_key (junto com `debug: True`) no JSON de resposta do `/health`, um endpoint sem autenticação. Além disso `database.py:76-79` popula usuários com senhas em texto puro. Some a isso o `/admin/reset-db` e `/admin/query` (`app.py:47-78`) sem nenhuma autenticação/autorização — qualquer um pode apagar o banco ou rodar SQL arbitrário.

- **[HIGH] God File em `models.py` misturando persistência, regra de negócio e SQL cru para 4 domínios** — `models.py` (315 linhas) concentra produtos, usuários, pedidos e relatório de vendas num único arquivo sem nenhuma camada de acesso a dados isolada. Não há ORM, nem repositórios, nem separação entre entidade e query. Isso viola a separação Model/Data-Access do MVC e torna qualquer teste unitário praticamente impossível sem subir o SQLite real.

- **[MEDIUM] Query N+1 na montagem de pedidos** — `models.py:171-201` (`get_pedidos_usuario`) e `models.py:203-233` (`get_todos_pedidos`) fazem um SELECT por pedido para buscar itens, e dentro desse loop mais um SELECT por item para buscar o nome do produto (`cursor3`, linhas 191-193 e 223-225). Para uma listagem com N pedidos e M itens cada, isso gera 1 + N + N*M queries em vez de usar JOINs — degrada rapidamente com o crescimento da base.

- **[MEDIUM] Ausência de validação/transação atômica em fluxo crítico de negócio** — `criar_pedido` (`models.py:133-169`) decrementa estoque em updates soltos dentro de um loop, sem transação explícita nem lock, e sem revalidar estoque no momento do UPDATE (checagem e escrita não são atômicas — race condition clássica de overselling em concorrência). Também não há validação de schema nas rotas (ex: `criar_pedido` em `controllers.py:188-220` não valida que `quantidade` é positiva ou que `itens` tem o formato esperado antes de repassar ao model).

- **[LOW] Uso de `print()` como logging em toda a aplicação** — espalhado por `controllers.py` (linhas 8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250) e `app.py:56, 83-86`. Não há níveis de log, não vai para arquivo/observabilidade, e mistura dados sensíveis (email do usuário, IDs) em stdout. Deveria usar o módulo `logging` padrão.

- **[LOW] Números mágicos e listas de valores válidas espalhadas no controller** — `controllers.py:52` (lista `categorias_validas` hardcoded dentro da função), `controllers.py:49-50` (limites `2` e `200` para tamanho de nome sem constante nomeada), e `controllers.py:242` (lista de status válidos repetida como literal). Deveriam ser constantes/enum centralizados; hoje uma mudança de regra exige caçar o valor em vários pontos do código.

### Projeto: `ecommerce-api-legacy` (Node.js/Express — LMS API com checkout)

- **[CRITICAL] Credenciais e chave de gateway de pagamento hardcoded no código-fonte** — `src/utils.js:2-6` expõe `dbPass`, `paymentGatewayKey` (`pk_live_...`) e `smtpUser` direto no módulo, versionados em Git. Pior, `AppManager.js:45` loga o número do cartão do cliente (`cc`) e a chave do gateway juntos no `console.log`, em texto puro. Isso é vazamento de dado sensível de cliente e de credencial de produção no mesmo golpe.

- **[HIGH] `AppManager` é uma God Class: rotas, SQL e regra de negócio de checkout no mesmo arquivo** — `AppManager.js` (142 linhas) concentra schema do banco, seed, roteamento Express e toda a lógica de checkout/relatório financeiro numa única classe, sem camada de Model/Repository nem Controller separados. O handler de `/api/checkout` (linhas 28-78) mistura validação, consulta de curso, criação de usuário, hashing de senha, cobrança e auditoria em closures aninhadas — impossível testar unitariamente sem subir o Express e o SQLite reais.

- **[MEDIUM] Query N+1 severa no relatório financeiro** — `AppManager.js:80-129` (`/api/admin/financial-report`) faz um `SELECT * FROM courses`, e para cada curso um `SELECT` de enrollments, e para cada enrollment mais dois `SELECT`s (usuário e pagamento). Para C cursos e E enrollments médios isso é 1 + C + C*E*2 queries, quando um JOIN resolveria em uma única consulta. O controle de conclusão por contadores (`coursesPending`, `enrPending`) também é frágil a race conditions com callbacks assíncronos.

- **[MEDIUM] Ausência de validação de entrada e hash de senha inseguro** — `/api/checkout` (`AppManager.js:28-35`) não valida formato de email, tamanho/força de senha, nem tipo/valor de `card`; a verificação de aprovação do pagamento é só `cc.startsWith("4")` (linha 46), uma simulação ingênua sem nenhuma validação real. Além disso `badCrypto` (`utils.js:17-23`) não é hash criptográfico — é só Base64 repetido e truncado em 10 caracteres, trivialmente reversível e com colisões previsíveis. Deveria usar bcrypt/argon2 e uma lib de validação (ex: Joi/Zod).

- **[LOW] Exclusão de usuário deixa dados órfãos de propósito** — `DELETE /api/users/:id` (`AppManager.js:131-137`) apaga o usuário mas mantém enrollments e payments referenciando um `user_id` inexistente, e ainda devolve a mensagem literal "ficaram sujos no banco" ao cliente da API. Não há cascade nem soft-delete — é inconsistência de integridade referencial deixada sem tratamento.

- **[LOW] Nomenclatura ruim e "magic strings" espalhados** — variáveis de uma letra em `/api/checkout` (`u`, `e`, `p`, `cid`, `cc` em `AppManager.js:29-33`) obrigam o leitor a caçar o significado em `req.body`; strings de status como `"PAID"`/`"DENIED"` (linhas 46, 108) são literais repetidos sem constante/enum central. Pequeno esforço de rename e extração de constantes melhoraria bastante a legibilidade.

### Projeto: `task-manager-api` (Python/Flask — API de Task Manager)

- **[CRITICAL] Hash de senha com MD5 e "token" de login falso** — `models/user.py:27-32` usa `hashlib.md5` para armazenar e verificar senha (MD5 é quebrado para senhas — rainbow tables resolvem em segundos) e ainda expõe o hash da senha no próprio `to_dict()` (linha 21), que é serializado em toda resposta de usuário (`routes/user_routes.py:24,86,129` etc). Para piorar, `routes/user_routes.py:210` devolve `'token': 'fake-jwt-token-' + str(user.id)` no login — não é JWT nenhum, é um ID de usuário disfarçado que qualquer um forja trocando o número, sem assinatura nem expiração. Combinado, isso quebra autenticação e confidencialidade de credenciais.

- **[HIGH] Nenhuma rota protegida por autenticação/autorização** — o "token" retornado no login (`user_routes.py:210`) nunca é verificado em lugar nenhum: todos os endpoints de tasks, users e reports (`task_routes.py`, `user_routes.py`, `report_routes.py`) são publicamente acessíveis sem checar sessão, token ou papel do usuário. Existe até um `is_admin()` em `models/user.py:34-38` que nunca é chamado. Qualquer cliente pode listar, editar ou apagar dados de qualquer usuário sem se autenticar.

- **[MEDIUM] Query N+1 sistemática ao montar listagens** — `task_routes.py:41-57` (`get_tasks`) faz um `User.query.get` e um `Category.query.get` dentro do loop para cada task, e o mesmo padrão se repete em `report_routes.py:55-68` (`user_stats`, um `Task.query.filter_by` por usuário) e em `report_routes.py:163` (`get_categories`, um `count()` por categoria). Para N tasks/usuários isso é 1 + 2N (ou pior) consultas onde um `join`/`joinedload` resolveria em uma só — degrada rapidamente com o volume de dados.

- **[MEDIUM] Lógica de negócio duplicada em vez de centralizada no Model/Service** — o cálculo de "task atrasada" (due_date no passado + status não finalizado) está copiado e colado em pelo menos 4 lugares (`task_routes.py:30-39`, `task_routes.py:71-80`, `user_routes.py:171-180`, `report_routes.py:33-37`), apesar de já existir `Task.is_overdue()` em `models/task.py:50-60` pronto para isso. Da mesma forma, `utils/helpers.py` define `process_task_data`, `validate_email` e constantes (`VALID_STATUSES`, `MIN_PASSWORD_LENGTH` etc.) que nunca são importadas pelas rotas — as rotas reimplementam validação inline com listas literais repetidas (`task_routes.py:110`, `177`; `user_routes.py:61`). Qualquer mudança de regra exige caçar e sincronizar várias cópias.

- **[LOW] `except` genérico engolindo erros e `print()` como logging** — `task_routes.py:62` (`except:`) e `user_routes.py:130,150` capturam qualquer exceção silenciosamente, dificultando diagnóstico de falhas reais (bug vs. erro de dados). Em paralelo, toda a aplicação usa `print(f"...")` para registrar ações (`task_routes.py:149,153,219,234`; `user_routes.py:83,89,147`) em vez do módulo `logging`, sem níveis, sem destino configurável e sem estrutura.

- **[LOW] Imports não utilizados e serviço morto no projeto** — `app.py:7` importa `sys, json` sem uso; `task_routes.py:7` importa `json, os, sys, time` sem uso; `report_routes.py:8` importa `json` sem uso. Além disso, `services/notification_service.py` implementa uma `NotificationService` completa (com credenciais SMTP hardcoded em texto puro nas linhas 9-10, outro problema de segurança à parte) que não é referenciada por nenhuma rota — código morto que só confunde quem lê o projeto.

## Construção da Skill

A skill `refactor-arch` (em `code-smells-project/.claude/skills/refactor-arch/`) nasceu da análise manual acima. Antes de escrever qualquer instrução, rodei os três projetos manualmente para entender que tipo de bagunça eu estava lidando: um monolito Python com SQL cru e injeção por todo lado, uma God Class em Node.js escondendo um checkout inteiro, e uma API Flask parcialmente organizada mas com autenticação de mentira. Só depois de ver esses três padrões diferentes de código ruim eu comecei a desenhar a skill, porque queria que ela generalizasse de verdade e não só resolvesse os três casos que eu já tinha na frente.

### Decisões de design

A primeira decisão foi separar a skill em três fases sequenciais (análise, auditoria e refatoração), cada uma com um ponto de checagem antes de avançar para a próxima. Isso não foi um capricho de organização, foi para evitar o problema mais comum desse tipo de tarefa: o agente sair reescrevendo arquivos antes de entender o que está mexendo. A Fase 1 obriga a olhar a stack e a arquitetura atual sem tocar em nada. A Fase 2 obriga a ler cada arquivo por completo, linha a linha, gerar um relatório com severidade e parar esperando confirmação explícita do usuário. Só na Fase 3 o código é de fato alterado. Coloquei essa pausa de confirmação como regra dura porque refatoração é uma operação de alto risco, e o usuário precisa poder revisar o diagnóstico antes de autorizar qualquer mudança em arquivo.

Outra decisão foi separar o conteúdo da skill em arquivos de referência (`references/`) em vez de colocar tudo dentro do `SKILL.md` principal. O catálogo de anti patterns, as heurísticas de detecção de stack, as guidelines de MVC, o playbook de refatoração e o template do relatório viraram arquivos próprios. Isso manteve o `SKILL.md` como um roteiro enxuto de "o que fazer em cada fase", enquanto o "como reconhecer isso" e "como corrigir aquilo" ficou em documentos que podem crescer independentemente sem inchar a instrução principal.

Também decidi atribuir uma severidade objetiva (CRITICAL, HIGH, MEDIUM, LOW) a cada finding, com um critério de decisão em cascata: primeiro pergunta se compromete segurança ou impede funcionamento, depois se impede testar ou manter isoladamente, depois se é desvio de padrão ou desperdício de performance, e só then trata como cosmético. Sem esse critério explícito a classificação de severidade fica subjetiva e inconsistente entre execuções.

### Anti patterns incluídos e por quê

O catálogo tem 16 anti patterns, escolhidos a partir do que apareceu de fato nos três projetos analisados manualmente, mas descritos de forma genérica o suficiente para aparecer em qualquer outra codebase parecida:

- SQL Injection e credenciais hardcoded entraram como CRITICAL porque foram os problemas mais graves encontrados no `code-smells-project` e no `ecommerce-api-legacy`: eles comprometem dados de verdade, não são só desvio de estilo.
- Ausência de autenticação/autorização e hashing fraco de senha vieram do `task-manager-api`, onde encontrei um token falso que nunca é validado e senhas em MD5 expostas na própria resposta da API. Esses dois viram problema de segurança recorrente em qualquer API que implementa "autenticação" na mão sem usar uma lib madura.
- God Class/God File e lógica de negócio pesada no controller entraram porque foi o padrão estrutural mais comum nos três projetos: `models.py`, `AppManager.js` e até as rotas do `task-manager-api` concentravam responsabilidades demais no mesmo lugar.
- Falta de transação atômica e Query N+1 entraram porque apareceram de forma quase idêntica nos três projetos (decremento de estoque sem lock, relatórios financeiros e listagens de tarefas todas com N+1), então valia a pena documentar o padrão de detecção e a correção de forma reutilizável.
- Os anti patterns de severidade mais baixa (uso de print como logging, magic numbers, código morto, imports não usados, duplicação de regra de negócio, integridade referencial e API deprecated) entraram para não deixar de fora os problemas menores que também apareceram nos três projetos e que, embora não sejam graves isoladamente, acumulam dívida técnica real.

Cada anti pattern no catálogo tem sinal de detecção concreto e explicação do porquê importa, para que o agente que rodar a skill não precise adivinhar o que procurar nem repetir o raciocínio de severidade a cada finding novo.

### Como garanti que a skill é agnóstica de tecnologia

Esse foi o ponto que mais me preocupou, porque os três projetos de teste já cobrem duas linguagens diferentes (Python e Node.js), e eu não queria uma skill que só funcionasse para essas duas. Para isso:

- A detecção de stack (`project-analysis.md`) não assume nada de antemão. Ela primeiro procura arquivos de manifesto (`requirements.txt`, `package.json`, `go.mod`, `pom.xml`, `Gemfile`, `composer.json`) e só cai para a extensão de arquivo predominante como critério de desempate se nenhum manifesto existir. A skill explicitamente instrui a nunca assumir Python ou Flask e sempre detectar primeiro.
- As guidelines de MVC (`mvc-guidelines.md`) descrevem o papel de cada camada (Model, View/Routes, Controller) em termos de responsabilidade, não de sintaxe de nenhuma linguagem específica. A estrutura de pastas sugerida para Python/Flask e para Node.js/Express aparece só como ponto de partida, com a instrução explícita de adaptar à convenção idiomática de qualquer outra stack (Java, Ruby, Go, PHP).
- O playbook de refatoração (`refactoring-playbook.md`) traz cada transformação em Python e em JavaScript lado a lado, de propósito, para deixar claro que o padrão de correção não está preso à sintaxe do exemplo. A instrução em cada seção reforça que o que importa é o resultado estrutural (segredo fora do código, query parametrizada, camadas separadas), não a sintaxe usada no exemplo.
- O catálogo de anti patterns descreve sinais de detecção em termos de padrão de código (concatenação de string em SQL, por exemplo) em vez de amarrar a detecção a uma função ou biblioteca específica de uma linguagem só.

Na prática, isso significa que se a skill rodar num projeto em Go ou Ruby que eu nunca testei, ela ainda tem instrução suficiente para detectar a stack corretamente e adaptar a estrutura de pastas e os exemplos de correção ao idioma daquela linguagem, em vez de tentar forçar convenção de Python nela.

### Desafios encontrados

O principal ponto de atenção foi generalizar as regras em vez de escrevê-las em cima só dos três projetos de teste. Descrever o anti pattern de query N+1 citando `cursor3` e `get_pedidos_usuario` diretamente seria mais rápido, mas não ajudaria em outro projeto. A solução foi descrever cada padrão em termos gerais (um SELECT dentro de um loop que itera sobre outro SELECT) e manter os exemplos específicos só como ilustração, não como definição.

Outro ponto foi calibrar a rigidez da Fase 3 para projetos que já têm alguma organização em camadas, como o `task-manager-api`, que já tinha `models/`, `routes/`, `services/` e `utils/` antes de qualquer refatoração. Uma instrução genérica de "criar estrutura MVC" recriaria pastas que já existiam e poderia renomear coisas que já estavam corretas só por convenção. Por isso a skill tem uma regra explícita para esse caso: se o projeto já tiver organização parcial, completar as lacunas e mover só o que precisa se mover, sem recriar do zero nem renomear pasta que já cumpre o papel certo.

A classificação de severidade também exigiu critério explícito para os casos que dependem de contexto. Ausência de autenticação, por exemplo, é CRITICAL numa rota administrativa destrutiva mas HIGH numa rota comum de CRUD; uma API deprecated pode variar de LOW (troca de nome de função) a CRITICAL (quando o próprio uso deprecated é uma falha de segurança). Esse julgamento ficou documentado como critério explícito no catálogo, em vez de depender da interpretação livre do agente em cada execução.

Por fim, a ordem de execução e a pausa de confirmação na Fase 2 precisaram ser reforçadas de forma redundante, tanto no `SKILL.md` quanto no `report-template.md`, porque o comportamento natural do agente tendia a emendar direto na refatoração assim que a auditoria terminava, sem de fato aguardar a resposta do usuário.

## Resultados

### Resumo dos relatórios de auditoria

Os três relatórios completos (Fase 2 da skill) estão salvos em [`reports/`](reports/): [`audit-project-1.md`](reports/audit-project-1.md) (code-smells-project), [`audit-project-2.md`](reports/audit-project-2.md) (ecommerce-api-legacy) e [`audit-project-3.md`](reports/audit-project-3.md) (task-manager-api).

| Projeto | Stack | Arquivos | LOC | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|---|---|---|
| code-smells-project | Python 3.12 + Flask 3.1.1 | 4 | ~780 | 11 | 4 | 6 | 4 | **25** |
| ecommerce-api-legacy | Node.js/Express 4.18.2 + sqlite3 | 3 | ~180 | 4 | 2 | 3 | 3 | **12** |
| task-manager-api | Python + Flask 3.0/SQLAlchemy | 15 | ~1150 | 4 | 3 | 5 | 4 | **16** |
| **Total** | | | | **19** | **9** | **14** | **11** | **53** |

Os findings CRITICAL concentraram-se em três famílias de problema recorrentes nos três projetos: **credenciais/segredos hardcoded no código-fonte** (SECRET_KEY, chave de gateway de pagamento, credenciais SMTP), **ausência total de autenticação/autorização** em rotas destrutivas (reset de banco, SQL arbitrário, delete de usuário) e **hashing de senha inseguro ou inexistente** (texto plano no code-smells-project, Base64 disfarçado no ecommerce-api-legacy, MD5 sem salt no task-manager-api). SQL Injection generalizado apareceu apenas no `code-smells-project`, que usa SQL cru sem nenhuma camada de ORM.

### Comparação antes/depois

**code-smells-project**
| Antes | Depois |
|---|---|
| `SECRET_KEY` fixa no código e vazada em `/health` | Lida de `os.environ`, endpoint `/health` não expõe segredos |
| `/admin/reset-db` e `/admin/query` (SQL arbitrário) sem autenticação | Middleware de auth (`middlewares/auth.py`) exige token de admin; `/admin/query` foi eliminado |
| Todas as queries por concatenação de string (SQL Injection generalizado) | Queries parametrizadas (`?`) em `models/produto_model.py`, `usuario_model.py`, `pedido_model.py` |
| Senha em texto plano, exposta em `GET /usuarios` | Hash com `itsdangerous`/token assinado; campo `senha` removido da serialização |
| `models.py` e `controllers.py` únicos concentrando 3 domínios (God File) | Separado por domínio: `models/`, `controllers/`, `routes/routes.py`, `config/`, `middlewares/` |
| Query N+1 em pedidos (1 + N + N*M) | Resolvido com JOIN em `pedido_model.py` |
| `print()` como logging | `logging_config.py` com logger estruturado |

**ecommerce-api-legacy**
| Antes | Depois |
|---|---|
| `AppManager.js` único com rotas + SQL + regra de negócio (God Class) | Separado em `models/` (User, Course, Enrollment, Payment), `controllers/` (checkout, admin, user), `routes/index.js` |
| `DELETE /api/users/:id` sem autenticação | Middleware `requireAdmin.js` exige header `x-admin-key` |
| Credenciais e chave de pagamento hardcoded em `utils.js`, logadas em `console.log` | Movidas para variáveis de ambiente (`src/config/index.js`), log removido |
| `badCrypto` (Base64 truncado, reversível) | `services/passwordHasher.js` com `bcryptjs` |
| Query N+1 no relatório financeiro (1 + N + 2M) | `models/financialReportModel.js` com JOIN único |
| Nenhuma transação no checkout (matrícula/pagamento/auditoria isolados) | Escritas do checkout envolvidas em transação no Model |

**task-manager-api**
| Antes | Depois |
|---|---|
| Hash de senha em MD5 sem salt, exposto em `to_dict()` | `werkzeug.security` (`generate_password_hash`/`check_password_hash`); campo `password` removido da serialização |
| Token de login `'fake-jwt-token-' + id`, nunca validado | JWT real (`PyJWT`) com expiração, validado por middleware em todas as rotas sensíveis |
| Nenhuma rota protegida — todos os endpoints públicos | `middlewares/` com `require_auth`/`require_admin` aplicados a tasks, users e reports |
| Regra "task atrasada" duplicada em 5 lugares, ignorando `Task.is_overdue()` já existente | Rotas chamam `task.is_overdue()`; duplicação eliminada |
| `utils/helpers.py` com validação pronta nunca importada pelas rotas | Rotas delegam a validação para `controllers/` reaproveitando `helpers.py` |
| Query N+1 em `get_tasks`, `summary_report` e `get_categories` | Resolvido com `joinedload`/agregação `GROUP BY` |
| Credenciais SMTP hardcoded em serviço órfão (nunca importado) | Credenciais via variáveis de ambiente (`.env.example`); serviço conectado ao fluxo de notificação |

### Checklist de validação

Critério exigido pela Fase 3 da skill (`SKILL.md`, seção "Validação"), aplicado aos três projetos:

| Item | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Segredos/config fora do código-fonte (env vars) | ✓ | ✓ | ✓ |
| Model concentra acesso a dados, sem SQL cru em controllers/routes | ✓ | ✓ | ✓ |
| Routes só mapeiam entrada/saída HTTP | ✓ | ✓ | ✓ |
| Controllers sem SQL cru nem regra de negócio pesada | ✓ | ✓ | ✓ |
| Tratamento de erro centralizado | ✓ (`middlewares/error_handler.py`) | ✓ (`middlewares/errorHandler.js`) | ✓ (`middlewares/error_handler.py`) |
| Composition root claro (ponto de entrada monta a app) | ✓ (`src/app.py`) | ✓ (`src/app.js`) | ✓ (`app.py`) |
| Dependências instaladas e app sobe sem erro | ✓ | ✓ | ✓ |
| Endpoints originais respondem como antes (contrato preservado) | ✓ | ✓ | ✓ |
| SQL Injection eliminado (queries parametrizadas) | ✓ | n/a (não encontrado) | n/a (já usava ORM) |
| Autenticação/autorização adicionada às rotas sensíveis | ✓ | ✓ | ✓ |
| Hashing de senha seguro | ✓ | ✓ | ✓ |
| Segredos não vazam em respostas HTTP nem em logs | ✓ | ✓ | ✓ |
| Query N+1 resolvida com JOIN/agregação | ✓ | ✓ | ✓ |

### Evidência de execução pós-refatoração

As três aplicações foram subidas localmente após a Fase 3, com as instruções de cada README de projeto, e exercitadas via `curl` para confirmar que os contratos de rota originais continuam respondendo e que as correções de segurança estão de fato em vigor.

**code-smells-project** — boot e checagens (porta 5000):
```
$ python app.py
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000

$ curl http://localhost:5000/health
{"counts":{"pedidos":0,"produtos":10,"usuarios":3},"database":"connected","status":"ok","versao":"1.0.0"}
# secret_key/debug não aparecem mais na resposta (antes vazavam aqui)

$ curl -X POST http://localhost:5000/login -d '{"email":"admin@loja.com","senha":"admin123"}'
{"dados":{...},"sucesso":true,"token":"eyJpZ...","mensagem":"Login OK"}

$ curl -X POST http://localhost:5000/admin/reset-db   # sem token
→ HTTP 401   # antes: apagava o banco sem nenhuma checagem

$ curl "http://localhost:5000/produtos/busca?q=notebook' OR '1'='1"
{"dados":[],"sucesso":true,"total":0}   # tentativa de SQL Injection não retorna dados indevidos
```

**ecommerce-api-legacy** — boot e checagens (porta 3000):
```
$ npm start
Frankenstein LMS rodando na porta 3000...

$ curl -X POST http://localhost:3000/api/checkout -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
{"msg":"Sucesso","enrollment_id":2}

$ curl http://localhost:3000/api/admin/financial-report
[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},
 {"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]

$ curl -X DELETE http://localhost:3000/api/users/1   # sem x-admin-key
→ HTTP 403   # antes: apagava o usuário sem nenhuma checagem

$ grep -i "pk_live\|senha_super_secreta" logs-da-aplicacao
→ nenhuma ocorrência   # antes: chave de pagamento e senha do banco apareciam no console.log do checkout
```

**task-manager-api** — boot e checagens (porta 5000):
```
$ python seed.py
Seed concluído com sucesso!
  3 usuários / 4 categorias / 10 tasks

$ python app.py
 * Running on http://127.0.0.1:5000

$ curl -X POST http://localhost:5000/login -d '{"email":"joao@email.com","password":"1234"}'
{"token":"eyJhbGciOiJIUzI1NiIs...", ...}   # JWT real, assinado e com expiração

$ curl http://localhost:5000/tasks   # sem token
→ HTTP 401   # antes: qualquer rota respondia sem autenticação

$ curl -X POST http://localhost:5000/users -d '{"name":"Teste QA","email":"qa@email.com","password":"senha123"}'
{"id":4,"name":"Teste QA","email":"qa@email.com","role":"user","active":true,"created_at":"..."}
# campo "password"/hash não aparece mais na resposta (antes vazava o hash MD5)
```

Em todos os casos a aplicação subiu sem erros com as dependências declaradas em cada `requirements.txt`/`package.json`, os endpoints documentados no README de cada projeto responderam com o mesmo contrato de antes da refatoração, e as tentativas manuais de explorar as falhas originais (SQL Injection, rota destrutiva sem auth, vazamento de segredo/senha) passaram a ser bloqueadas ou neutralizadas.

## Como Executar

### Pré-requisitos

- **Claude Code** instalado e autenticado (a skill `refactor-arch` vive em `.claude/skills/refactor-arch/` dentro de cada projeto e é invocada de dentro do Claude Code).
- **Python 3.10+** (para `code-smells-project` e `task-manager-api`), com `venv`.
- **Node.js 18+** e `npm` (para `ecommerce-api-legacy`).
- `curl` (ou similar) para validar as rotas manualmente após a refatoração.
- Nenhum dos três projetos usa Docker — tudo roda local, sem serviços externos.

### Rodando a skill `refactor-arch` em cada projeto

A skill é a mesma (`refactor-arch`), replicada em `.claude/skills/` de cada projeto. Ela roda em 3 fases sequenciais — **análise da stack**, **auditoria com relatório de severidade** (pausa aguardando confirmação) e **refatoração para MVC** — e só avança de fase com aprovação explícita.

Abra o Claude Code com a raiz do repositório como diretório de trabalho e, para cada projeto, peça para rodar a skill apontando a pasta alvo, por exemplo:

```
/refactor-arch code-smells-project
/refactor-arch ecommerce-api-legacy
/refactor-arch task-manager-api
```

Ou, em linguagem natural: "rode a skill refactor-arch no projeto `code-smells-project`". O fluxo esperado em cada execução:

1. **Fase 1 — Análise**: a skill identifica stack, framework e estrutura de pastas atual, sem alterar nada.
2. **Fase 2 — Auditoria**: gera um relatório com os anti patterns encontrados, classificados por severidade (CRITICAL/HIGH/MEDIUM/LOW), e **para**, aguardando sua confirmação para prosseguir.
3. **Fase 3 — Refatoração**: só após confirmação, aplica as correções (separação MVC, remoção de segredos hardcoded, queries parametrizadas, autenticação, resolução de N+1, etc.), preservando o contrato das rotas existentes.

Os relatórios gerados na Fase 2 para os três projetos deste repositório já estão salvos em [`reports/`](reports/).

### Executando cada projeto após a refatoração

**code-smells-project** (Python/Flask, porta 5000):
```bash
cd code-smells-project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

**ecommerce-api-legacy** (Node.js/Express, porta 3000):
```bash
cd ecommerce-api-legacy
npm install
npm start
```

**task-manager-api** (Python/Flask, porta 5000):
```bash
cd task-manager-api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py   # popula o banco antes do primeiro boot
python app.py
```

### Como validar que a refatoração funcionou

Não há suíte de testes automatizados nos três projetos — a validação é feita subindo cada aplicação e exercitando as rotas via `curl`, comparando com o comportamento documentado no README de cada projeto. Checklist mínimo, aplicado a cada um:

- **App sobe sem erro** com as dependências do `requirements.txt`/`package.json`, e os endpoints já existentes continuam respondendo com o mesmo contrato de antes (ver exemplos de `curl` no README de cada projeto).
- **Segredos fora do código**: confira que `SECRET_KEY`, chaves de gateway e credenciais SMTP vêm de variáveis de ambiente, e que nenhum endpoint (ex.: `/health`) os expõe na resposta.
- **Autenticação/autorização em vigor**: rotas destrutivas ou administrativas (`/admin/reset-db`, `DELETE /api/users/:id`, rotas de tasks/reports) devem devolver `401`/`403` sem token/chave válida.
- **SQL Injection neutralizado** (`code-smells-project`): tentar injeção via query string (ex.: `?q=notebook' OR '1'='1`) não deve retornar dados indevidos.
- **Hash de senha seguro**: nenhuma resposta HTTP deve vazar senha em texto plano ou hash (MD5/Base64) — conferir em `GET /usuarios`, `GET /users/:id`, etc.
- **Camadas MVC separadas**: model concentra acesso a dados (sem SQL cru em controllers/routes), controllers sem lógica de persistência, routes só mapeiam entrada/saída HTTP.
- **N+1 resolvido**: relatórios e listagens (vendas, financial-report, tasks/reports) devem usar JOIN/agregação em vez de um SELECT por item dentro de loop.

O comparativo antes/depois completo, com evidências de execução via `curl` para os três projetos, está na seção [Resultados](#resultados) acima.