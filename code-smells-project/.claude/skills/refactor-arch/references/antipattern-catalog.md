# Catálogo de Anti Patterns

Este catálogo lista os anti patterns que a auditoria (Fase 2) deve procurar em qualquer codebase de backend, com os sinais concretos de detecção e a severidade correspondente. A escala de severidade segue a definição abaixo, baseada em violações de MVC e SOLID.

## Escala de severidade

- **CRITICAL**: falha grave de arquitetura ou segurança que impede o funcionamento correto, expõe dados sensíveis, ou viola completamente a separação de responsabilidades.
- **HIGH**: forte violação do padrão MVC ou de princípios SOLID que dificulta muito manutenção e testes.
- **MEDIUM**: problema de padronização, duplicação de código ou gargalo de performance moderada.
- **LOW**: melhoria de legibilidade, nomenclatura ruim, ou magic numbers.

Ao classificar um finding, pergunte primeiro "isso compromete segurança ou impede o funcionamento correto?" (CRITICAL), depois "isso impede testar ou manter essa parte do código isoladamente?" (HIGH), depois "isso é um desvio de padrão ou desperdício de performance perceptível?" (MEDIUM), e só then trate como cosmético (LOW).

## 1. SQL Injection (CRITICAL)

**Sinais de detecção**: strings SQL montadas por concatenação ou f-string/template literal com valores vindos direto do request (`f"SELECT * FROM x WHERE id = {id}"`, `"SELECT * FROM x WHERE id = " + id`, `query = \`SELECT * FROM ${table}\``). Também conta quando um endpoint executa SQL arbitrário recebido no corpo da requisição.

**Por que importa**: permite a um atacante ler, alterar ou apagar qualquer dado do banco, e em muitos drivers também executar comandos administrativos.

## 2. Credenciais e segredos hardcoded (CRITICAL)

**Sinais de detecção**: `SECRET_KEY`, senha de banco, chave de API de pagamento, credencial de SMTP ou qualquer segredo escrito literalmente no código fonte, em vez de vir de variável de ambiente ou de um cofre de segredos. Também conta quando um segredo é devolvido em uma resposta HTTP, mesmo que a origem dele já esteja em variável de ambiente.

**Por que importa**: qualquer pessoa com acesso ao repositório (ou ao endpoint que vaza o segredo) ganha acesso a sistemas de produção.

## 3. Ausência de autenticação e autorização (CRITICAL ou HIGH)

**Sinais de detecção**: rotas administrativas ou destrutivas (reset de banco, execução de SQL, exclusão de recursos) sem nenhuma checagem de identidade; um mecanismo de "token" que existe mas nunca é validado nas rotas; função de checagem de papel (`is_admin`) definida mas nunca chamada.

**Por que importa**: qualquer cliente da API pode ler ou modificar dados de qualquer usuário, ou executar ações administrativas. Classifique como CRITICAL quando a rota exposta é destrutiva ou administrativa, e como HIGH quando é uma ausência geral de autorização em rotas de CRUD comuns.

## 4. Hashing ou criptografia fraca de senha (CRITICAL)

**Sinais de detecção**: uso de `md5`, `sha1` sem salt, Base64 disfarçado de hash, ou qualquer esquema caseiro para "proteger" senha em vez de um algoritmo desenhado para isso (bcrypt, scrypt, argon2). Também conta armazenar ou retornar a senha (ou seu hash) em texto acessível na resposta da API.

**Por que importa**: credenciais vazadas do banco são trivialmente revertidas, comprometendo contas de usuários em outros sistemas também (reuso de senha).

## 5. God Class / God File (CRITICAL ou HIGH)

**Sinais de detecção**: um único arquivo ou classe concentrando roteamento, acesso a dados (SQL cru) e regra de negócio para múltiplos domínios diferentes (por exemplo produtos, usuários e pedidos no mesmo arquivo). Classifique como CRITICAL quando o arquivo mistura banco de dados, lógica complexa e roteamento HTTP todos juntos; como HIGH quando concentra várias responsabilidades mas ao menos separa rota de acesso a dados em alguma medida.

**Por que importa**: impossibilita teste unitário isolado, qualquer mudança pequena arrisca quebrar funcionalidades não relacionadas.

## 6. Lógica de negócio pesada dentro de Controller ou Route (HIGH)

**Sinais de detecção**: handler de rota que faz validação complexa, cálculo de negócio, orquestração de múltiplas escritas no banco e formatação de resposta tudo na mesma função, sem delegar a um Model ou Service.

**Por que importa**: a regra de negócio fica acoplada ao transporte HTTP, dificultando reuso e testes automatizados sem subir um servidor.

## 7. Falta de transação atômica em fluxo crítico (HIGH ou MEDIUM)

**Sinais de detecção**: múltiplas escritas relacionadas (por exemplo debitar estoque de vários itens de um pedido) feitas em updates soltos, sem transação nem lock, sem revalidar o estado no momento da escrita. Classifique como HIGH quando o fluxo envolve dinheiro ou estoque (risco direto de perda financeira), como MEDIUM quando o impacto é mais limitado.

**Por que importa**: sob concorrência, duas requisições podem passar pela mesma checagem antes de qualquer uma escrever, causando overselling ou inconsistência de dados (race condition clássica de check-then-act).

## 8. Query N+1 (MEDIUM)

**Sinais de detecção**: um SELECT dentro de um loop que itera sobre o resultado de outro SELECT (por exemplo buscar itens de cada pedido, um pedido por vez, e dentro buscar o nome de cada produto, um produto por vez). Em ORMs, o mesmo padrão aparece como acesso a um relacionamento lazy dentro de um loop sem `join`/`joinedload`/`select_related`.

**Por que importa**: o número de queries cresce proporcionalmente ao volume de dados (1 + N ou 1 + N*M), degradando performance rapidamente à medida que a base cresce, quando um JOIN resolveria em uma única consulta.

## 9. Ausência de validação de entrada (MEDIUM)

**Sinais de detecção**: rota que repassa direto ao model/banco um campo do corpo da requisição sem checar tipo, formato, obrigatoriedade ou faixa de valor (quantidade negativa, email sem `@`, string vazia aceita como nome).

**Por que importa**: abre espaço para dados inconsistentes no banco e para erros que só aparecem em camadas mais profundas da aplicação, difíceis de rastrear até a causa raiz.

## 10. Uso de API ou função deprecated (MEDIUM a CRITICAL conforme o caso)

**Sinais de detecção**: chamadas a métodos, módulos ou padrões marcados como deprecated pela própria linguagem ou framework em uso. Exemplos comuns a procurar:

- Python: `datetime.utcnow()` (deprecated desde 3.12, usar `datetime.now(timezone.utc)`), `imp` (usar `importlib`), acesso a atributo de `flask.Markup` fora de `markupsafe`, `pkg_resources` deprecated (usar `importlib.metadata`)
- Node.js/Express: middlewares `bodyParser.json()` embutidos no próprio `body-parser` quando o Express >= 4.16 já expõe `express.json()`; `new Buffer(...)` (deprecated e inseguro, usar `Buffer.from(...)`); callbacks de `fs` antigos quando o projeto já usa `fs/promises` em outros pontos; `String.prototype.substr` (deprecated, usar `slice`/`substring`)
- Genérico: qualquer dependência no manifesto com uma major version claramente antiga e com CVE conhecido, ou qualquer comentário/changelog no próprio pacote alertando remoção futura da API usada

Ao encontrar um uso desses, sempre reporte tanto o que está deprecated quanto o equivalente moderno recomendado na recomendação do finding. Classifique a severidade pelo impacto real (uma API deprecated que também é uma falha de segurança é CRITICAL; uma que é só uma troca de nome de função é LOW ou MEDIUM).

## 11. Duplicação de lógica de negócio (MEDIUM)

**Sinais de detecção**: a mesma regra de negócio (por exemplo, cálculo de "está atrasado") implementada de forma independente em vários arquivos, especialmente quando já existe um método pronto no Model para isso mas não é chamado, ou quando existe um módulo de utilitários com a validação certa mas as rotas reimplementam a validação inline.

**Por que importa**: qualquer mudança de regra exige encontrar e sincronizar múltiplas cópias, e é fácil esquecer uma, criando comportamento inconsistente entre endpoints.

## 12. Tratamento de erro genérico ou ausente (LOW ou MEDIUM)

**Sinais de detecção**: `except:` nu sem especificar o tipo de exceção, blocos catch vazios, ou ausência total de tratamento de erro em operações que podem falhar (parse de JSON, acesso a banco, chamada externa). Classifique como MEDIUM quando isso pode mascarar falhas silenciosas em fluxo crítico, LOW quando o impacto é apenas de diagnóstico.

**Por que importa**: engolir exceções sem logar ou diferenciar o tipo de erro dificulta diagnosticar se uma falha é um bug real ou um erro esperado de dado do usuário.

## 13. Uso de print como logging (LOW)

**Sinais de detecção**: chamadas a `print()`, `console.log()` espalhadas pela aplicação para registrar eventos de negócio, em vez de um logger estruturado (`logging` em Python, `winston`/`pino` em Node), especialmente quando dados sensíveis (email, id de usuário, número de cartão) aparecem nesses logs.

**Por que importa**: não há níveis de severidade, não há como redirecionar para um sistema de observabilidade, e é fácil vazar dado sensível em stdout sem perceber.

## 14. Magic numbers, magic strings e nomenclatura ruim (LOW)

**Sinais de detecção**: literais soltos no meio do código de negócio sem constante nomeada (limites de tamanho, listas de categorias ou status válidos repetidas em mais de um lugar), e identificadores de uma letra ou sem significado (`u`, `e`, `cc`, `cid`) em funções que não sejam laços triviais.

**Por que importa**: obriga o leitor a caçar o significado de cada valor ou nome pelo contexto, e qualquer mudança de regra exige encontrar todas as ocorrências espalhadas manualmente.

## 15. Código morto e imports não utilizados (LOW)

**Sinais de detecção**: imports no topo do arquivo nunca referenciados no corpo; módulos, classes ou serviços completos implementados mas nunca chamados por nenhuma rota ou outro módulo.

**Por que importa**: aumenta a superfície de código para ler e manter sem entregar valor, e pode confundir quem lê o projeto pensando que aquela funcionalidade está ativa quando não está.

## 16. Inconsistência de integridade referencial (LOW ou MEDIUM)

**Sinais de detecção**: exclusão de um registro que deixa referências órfãs em outras tabelas (chave estrangeira apontando para um id que não existe mais), sem cascade nem soft-delete nem qualquer tratamento.

**Por que importa**: consultas futuras que dependem dessa referência podem falhar ou retornar dado inconsistente, e o problema só aparece bem depois da causa raiz (a exclusão), dificultando o diagnóstico.
