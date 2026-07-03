================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.12 + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
CRITICAL: 11 | HIGH: 4 | MEDIUM: 6 | LOW: 4

## Findings

### [CRITICAL] Configuração insegura hardcoded no código-fonte (SECRET_KEY e DEBUG)
File: app.py:7-8, 88
Description: `app.config["SECRET_KEY"]` é definida com o literal `"minha-chave-super-secreta-123"` e `app.config["DEBUG"] = True` é fixado no código-fonte; `app.run(..., debug=True)` na linha 88 mantém o debugger interativo do Werkzeug ativo mesmo fora de desenvolvimento.
Impact: Qualquer pessoa com acesso ao repositório conhece a SECRET_KEY usada para assinar sessões/tokens, e o debug mode exposto publicamente permite execução arbitrária de código via o console interativo do Werkzeug.
Recommendation: Mover SECRET_KEY e DEBUG para variáveis de ambiente carregadas por um módulo de config dedicado, com debug desabilitado por padrão fora de desenvolvimento.

### [CRITICAL] Rota administrativa destrutiva sem autenticação (/admin/reset-db)
File: app.py:47-57
Description: O endpoint `POST /admin/reset-db` apaga todos os registros de `itens_pedido`, `pedidos`, `produtos` e `usuarios` sem nenhuma checagem de identidade ou papel do requisitante.
Impact: Qualquer cliente da API, autenticado ou não, pode apagar o banco de dados inteiro com uma única requisição.
Recommendation: Remover a rota do fluxo público ou protegê-la com autenticação de administrador obrigatória, aplicando um middleware de autorização antes de delegar ao Model.

### [CRITICAL] Execução de SQL arbitrário recebido no corpo da requisição (/admin/query)
File: app.py:59-78
Description: O endpoint `POST /admin/query` pega a string em `dados.get("sql", "")` e executa diretamente via `cursor.execute(query)`, sem autenticação, validação ou allowlist de comandos.
Impact: Qualquer cliente da API pode ler, alterar ou apagar qualquer dado do banco, incluindo senhas de usuários, executando SQL arbitrário.
Recommendation: Eliminar esse endpoint por completo; qualquer operação administrativa legítima deve ser exposta como uma rota específica e validada, nunca como execução de SQL livre.

### [CRITICAL] Segredo vazado na resposta HTTP do health check
File: controllers.py:264-292 (linha 289)
Description: `health_check()` devolve `"secret_key": "minha-chave-super-secreta-123"` e `"debug": True` diretamente no corpo JSON da rota pública `/health`.
Impact: Qualquer chamada não autenticada a `/health` revela a SECRET_KEY da aplicação, permitindo forjar sessões ou tokens assinados com ela.
Recommendation: Remover completamente os campos `secret_key` e `debug` da resposta; um health check deve expor no máximo status de conectividade, nunca segredos de configuração.

### [CRITICAL] Senha armazenada e comparada em texto plano
File: models.py:105-131 (login_usuario, criar_usuario)
Description: `criar_usuario` insere `senha` recebida do request diretamente na coluna `senha` sem qualquer hashing, e `login_usuario` autentica comparando a senha em texto plano dentro do próprio `WHERE` do SQL (`AND senha = '...'`).
Impact: Um vazamento do banco de dados expõe todas as senhas em texto puro, comprometendo também outras contas dos usuários que reutilizam senha em outros sistemas.
Recommendation: Gerar hash da senha com bcrypt/argon2 no momento do cadastro e comparar hashes no login, nunca comparar ou armazenar a senha em claro.

### [CRITICAL] Exposição de senha nas respostas da API
File: models.py:72-103 (get_todos_usuarios, get_usuario_por_id)
Description: `get_todos_usuarios` (linha 83) e `get_usuario_por_id` (linha 99) incluem o campo `"senha": row["senha"]` no dicionário retornado, que é serializado diretamente como JSON pelos controllers `listar_usuarios` e `buscar_usuario`.
Impact: Qualquer chamada a `GET /usuarios` ou `GET /usuarios/<id>` devolve a senha de qualquer usuário do sistema, mesmo sem autenticação.
Recommendation: Excluir o campo `senha` (ou seu hash) de qualquer serialização de usuário destinada a resposta HTTP.

### [CRITICAL] SQL Injection em operações de Produtos
File: models.py:24-70 (get_produto_por_id:28, criar_produto:47-50, atualizar_produto:57-61, deletar_produto:68)
Description: Todas as queries de produto são montadas por concatenação de string com valores vindos do request (`nome`, `descricao`, `preco`, `estoque`, `categoria`) ou da URL (`id`), sem parâmetros preparados.
Impact: Um atacante pode injetar SQL no campo `nome` ou `descricao` ao criar/atualizar um produto (ex: `nome` contendo `'); DROP TABLE produtos;--`) para ler, alterar ou apagar dados arbitrários.
Recommendation: Reescrever todas as queries usando placeholders parametrizados (`?`) do sqlite3, nunca concatenar valores de entrada na string SQL.

### [CRITICAL] SQL Injection na busca pública de produtos
File: models.py:285-314 (buscar_produtos)
Description: Os parâmetros `termo` e `categoria`, vindos diretamente de `request.args` sem validação, são concatenados na cláusula `WHERE`/`LIKE` da query (linhas 291 e 293) em um endpoint público (`GET /produtos/busca`) que não exige autenticação.
Impact: Qualquer visitante não autenticado pode explorar SQL Injection apenas manipulando a query string, por exemplo `?q=' OR '1'='1`, para extrair dados de qualquer tabela do banco.
Recommendation: Usar queries parametrizadas para `termo` e `categoria`, montando a cláusula `LIKE` com placeholders (`?`) em vez de concatenação.

### [CRITICAL] SQL Injection em Usuários e bypass de autenticação no Login
File: models.py:89-131 (get_usuario_por_id:92, login_usuario:109-111, criar_usuario:126-129)
Description: `login_usuario` monta `SELECT * FROM usuarios WHERE email = '<email>' AND senha = '<senha>'` por concatenação direta dos campos do corpo da requisição de login.
Impact: Um atacante pode autenticar como qualquer usuário sem conhecer a senha, por exemplo enviando `email` = `admin@loja.com' --`, contornando completamente a autenticação.
Recommendation: Usar queries parametrizadas para todas as operações de usuário, e nunca autenticar comparando senha em claro dentro do próprio SQL (ver finding de hashing de senha).

### [CRITICAL] SQL Injection no fluxo de Pedidos
File: models.py:133-283 (criar_pedido:140,148-151,155-166; get_pedidos_usuario:174,188,192; get_todos_pedidos:206,220,224; atualizar_status_pedido:279-280)
Description: A criação de pedido concatena `produto_id` e `quantidade` vindos do corpo da requisição (itens do pedido) diretamente nas queries de SELECT/INSERT/UPDATE, e as demais funções de listagem/atualização de pedido repetem o mesmo padrão de concatenação.
Impact: Um atacante pode injetar SQL através do campo `produto_id` de um item de pedido (`POST /pedidos`), comprometendo o banco a partir de um fluxo de checkout público.
Recommendation: Parametrizar todas as queries do módulo de pedidos com placeholders (`?`), incluindo as usadas dentro dos laços de itens.

### [HIGH] Ausência de autorização em todas as rotas de CRUD
File: app.py:11-30
Description: Existe uma rota `/login` (controllers.login) mas ela não gera nenhum token de sessão, e nenhuma das rotas de produtos, usuários ou pedidos valida identidade ou papel do requisitante antes de executar a ação.
Impact: Qualquer cliente da API pode listar, criar, alterar ou apagar produtos e ver pedidos de qualquer usuário sem se autenticar.
Recommendation: Implementar emissão de token no login (ex: JWT) e um middleware de autenticação/autorização aplicado às rotas que exigem usuário logado.

### [HIGH] God File — regras de negócio de múltiplos domínios concentradas em controllers.py e models.py
File: controllers.py:1-292, models.py:1-314
Description: `controllers.py` concentra handlers de produtos, usuários e pedidos no mesmo arquivo, incluindo validação de negócio; `models.py` concentra acesso a dados cru (SQL) para os mesmos três domínios sem nenhuma camada intermediária de Model orientada a objeto.
Impact: Qualquer mudança em uma regra de um domínio (ex.: pedidos) exige navegar um arquivo enorme que mistura outros domínios, aumentando o risco de quebrar funcionalidade não relacionada.
Recommendation: Separar controllers e models por domínio (produto, usuario, pedido) em módulos próprios, como já demonstrado na estrutura MVC alvo.

### [HIGH] Lógica de negócio pesada dentro do Controller
File: controllers.py:24-62 (criar_produto), 188-220 (criar_pedido)
Description: `criar_produto` faz validação de obrigatoriedade, faixa de valor e lista de categorias válidas diretamente no handler da rota; `criar_pedido` orquestra a chamada ao model e dispara efeitos colaterais (envio de "email"/"SMS"/"push" simulado via print) tudo na mesma função.
Impact: Essas regras não podem ser testadas isoladamente sem subir um servidor HTTP, e qualquer reuso da mesma validação em outro fluxo exige duplicar o código.
Recommendation: Mover validação e orquestração de negócio para o Model/Service correspondente, deixando o Controller apenas repassar entrada e formatar a resposta.

### [HIGH] Falta de transação atômica na criação de pedido (risco de overselling de estoque)
File: models.py:133-169
Description: `criar_pedido` verifica `produto["estoque"] < item["quantidade"]` e, em um laço separado, decrementa o estoque com `UPDATE produtos SET estoque = estoque - ...`, sem transação nem lock entre a checagem e a escrita.
Impact: Sob concorrência, duas requisições de compra simultâneas podem passar pela checagem de estoque antes de qualquer uma escrever, causando venda de estoque negativo (overselling).
Recommendation: Envolver a checagem e o decremento de estoque em uma transação atômica, revalidando o estoque no momento do `UPDATE` (ex.: `UPDATE ... WHERE estoque >= quantidade` e checar linhas afetadas).

### [MEDIUM] Query N+1 na listagem de pedidos
File: models.py:171-201 (get_pedidos_usuario), 203-233 (get_todos_pedidos)
Description: Para cada pedido retornado pela query principal, o código abre um novo cursor para buscar seus itens, e para cada item abre outro cursor para buscar o nome do produto (`cursor2`, `cursor3` dentro de laços aninhados).
Impact: O número de queries cresce proporcionalmente ao número de pedidos e itens, tornando `GET /pedidos` cada vez mais lento à medida que a base cresce.
Recommendation: Substituir os laços aninhados por uma única query com `JOIN` entre `pedidos`, `itens_pedido` e `produtos`, agregando o resultado em memória.

### [MEDIUM] Ausência de validação de entrada nos itens do pedido
File: controllers.py:188-220 (criar_pedido)
Description: O handler valida apenas a presença de `usuario_id` e que `itens` não é vazio, mas não valida que `produto_id` é um inteiro válido nem que `quantidade` é um número positivo antes de repassar ao Model.
Impact: Uma requisição com `quantidade` negativa ou zero, ou `produto_id` de tipo inesperado, pode gerar pedidos inconsistentes ou incrementar estoque em vez de decrementar.
Recommendation: Validar tipo e faixa de `produto_id`/`quantidade` no Controller (ou em uma camada de validação) antes de chamar o Model.

### [MEDIUM] Duplicação de validação entre criar_produto e atualizar_produto
File: controllers.py:24-96
Description: As checagens de obrigatoriedade de `nome`/`preco`/`estoque` e de valores negativos aparecem duplicadas quase palavra por palavra entre `criar_produto` (24-62) e `atualizar_produto` (64-96).
Impact: Uma mudança de regra (ex.: novo campo obrigatório) precisa ser replicada manualmente nos dois lugares, com risco de esquecer um deles e gerar comportamento inconsistente.
Recommendation: Extrair a validação comum para uma função única (no Model ou em um validador compartilhado) reutilizada pelos dois handlers.

### [MEDIUM] Tratamento de erro genérico expõe detalhes internos ao cliente
File: controllers.py (padrão repetido em todas as 20 funções, ex.: linhas 10-12, 60-62, 218-220)
Description: Todo handler captura `except Exception as e` de forma genérica e devolve `str(e)` diretamente no JSON de resposta, sem diferenciar tipo de erro nem logar de forma estruturada.
Impact: Uma exceção inesperada (ex.: erro de driver SQL) pode vazar detalhes internos da implementação, como nomes de tabela ou coluna, diretamente para o cliente da API.
Recommendation: Centralizar o tratamento de erro em um handler único que loga a exceção completa internamente e devolve ao cliente apenas uma mensagem genérica e um código apropriado.

### [MEDIUM] Inconsistência de integridade referencial ao deletar produto
File: models.py:65-70 (deletar_produto)
Description: `deletar_produto` remove a linha de `produtos` sem checar ou tratar as referências existentes em `itens_pedido.produto_id` para aquele produto.
Impact: Pedidos antigos passam a referenciar um `produto_id` inexistente; `get_pedidos_usuario`/`get_todos_pedidos` já mitigam parcialmente exibindo "Desconhecido", mas o dado fica inconsistente sem qualquer registro do que ocorreu.
Recommendation: Adotar soft-delete (`ativo = 0`, campo já existente na tabela mas não usado por `deletar_produto`) em vez de exclusão física, preservando o histórico de pedidos.

### [LOW] Uso de print como logging, incluindo dados sensíveis
File: controllers.py:161,179,182,208-210 (email do usuário), app.py:56,83-86
Description: Eventos de negócio (login, criação de usuário, criação de pedido) são registrados com `print()`, e em vários pontos o e-mail do usuário é impresso diretamente em stdout (`"Login bem-sucedido: " + email`, `"Usuário criado: " + email`).
Impact: Não há níveis de severidade nem redirecionamento para um sistema de observabilidade, e dados pessoais (e-mail) ficam expostos em logs de stdout sem controle de acesso.
Recommendation: Substituir os `print()` por um logger estruturado (`logging`), evitando registrar diretamente dados pessoais sensíveis.

### [LOW] Magic strings duplicadas para categorias e status válidos
File: controllers.py:52, 242
Description: A lista de categorias válidas (`["informatica", "moveis", ...]`) e a lista de status válidos (`["pendente", "aprovado", ...]`) estão declaradas como literais soltos dentro das funções que as usam, sem constante nomeada nem fonte única.
Impact: Adicionar uma nova categoria ou status exige localizar manualmente todas as ocorrências espalhadas pelo código, com risco de esquecer alguma e gerar validação inconsistente entre rotas.
Recommendation: Extrair essas listas para constantes nomeadas (ou um Enum) em um módulo compartilhado, referenciado por todos os pontos que validam esses valores.

### [LOW] Import não utilizado
File: database.py:2 (import os), models.py:2 (import sqlite3)
Description: `database.py` importa o módulo `os` e `models.py` importa `sqlite3` diretamente, mas nenhum dos dois é referenciado no corpo dos respectivos arquivos.
Impact: Aumenta a superfície de leitura do arquivo sem entregar valor, e pode sugerir a um leitor que há uso de variáveis de ambiente ou de tipos do sqlite3 que na verdade não existe.
Recommendation: Remover os imports não utilizados.

### [LOW] Caminho do banco de dados hardcoded no código-fonte
File: database.py:5 (db_path = "loja.db")
Description: O caminho do arquivo SQLite está fixado como literal no código-fonte, em vez de vir de uma variável de ambiente ou de um módulo de configuração.
Impact: Trocar o ambiente (teste, produção) ou o local do arquivo de banco exige editar o código-fonte diretamente.
Recommendation: Mover `db_path` para uma variável de ambiente (ex.: `DB_PATH`) lida por um módulo de configuração dedicado.

================================
Total: 25 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
