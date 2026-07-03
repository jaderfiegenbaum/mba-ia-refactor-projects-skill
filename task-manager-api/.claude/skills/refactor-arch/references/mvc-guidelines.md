# Guidelines de Arquitetura MVC

Este arquivo define o padrão MVC alvo da refatoração, agnóstico de linguagem. As três camadas abaixo devem sempre existir e estar fisicamente separadas em arquivos ou pastas diferentes, independente da stack. Os nomes de pasta seguem a convenção idiomática de cada linguagem, mas o papel de cada camada é o mesmo em qualquer stack.

## Model

Responsável por representar os dados do domínio e por todo acesso a persistência (banco de dados, cache, arquivos). É a única camada que deve conter SQL, chamadas de ORM, ou qualquer forma de leitura e escrita em um armazenamento externo.

Um Model deve:

- Expor operações de domínio com nomes claros (`criar_pedido`, `buscar_por_id`, `listar_atrasadas`), não expor SQL cru para quem chama.
- Concentrar regra de negócio que depende diretamente dos dados (por exemplo, "uma task está atrasada se `due_date` já passou e o status não é `done`") em um único lugar, reutilizável por qualquer camada superior.
- Usar parâmetros de query (`?`, `%s`, bind de ORM) para qualquer valor vindo de fora, nunca concatenação de string.
- Não conhecer nada sobre HTTP: não deve receber um objeto de request nem devolver um JSON pronto para resposta.

Um Model não deve: montar resposta HTTP, ler `request.body` diretamente, ou chamar outro Model de domínio diferente sem necessidade.

## View / Routes

Responsável por mapear a entrada e a saída HTTP: qual rota existe, qual método aceita, como o corpo da requisição chega até o Controller e como o retorno do Controller vira uma resposta HTTP (status code, corpo, headers).

Uma View/Route deve:

- Declarar o endpoint e delegar imediatamente ao Controller correspondente.
- Não conter regra de negócio nem acesso direto a dados.
- Fazer, no máximo, validação estrutural simples de payload (presença de campos obrigatórios, tipo básico), delegando validação de regra de negócio ao Controller ou Model.

Em frameworks que renderizam HTML (não é o caso destes 3 projetos, que são APIs), a View também cobriria templates. Como os projetos alvo são todos APIs REST, "View" aqui equivale à camada de rotas.

## Controller

Responsável por orquestrar o fluxo de uma requisição: receber os dados já mapeados pela Route, validar regra de negócio de mais alto nível, chamar um ou mais Models, e formatar o resultado para devolver à Route.

Um Controller deve:

- Conter a lógica de orquestração de uma operação (por exemplo, "criar pedido" chama o Model de estoque, depois o Model de pedido, dentro de uma transação).
- Validar entrada de negócio (quantidade positiva, status permitido) antes de chamar o Model.
- Formatar a resposta (o dicionário ou objeto que a Route vai serializar), sem se preocupar com o transporte HTTP em si (status code fica a cargo da Route, ou o Controller retorna um resultado que a Route traduz).

Um Controller não deve: escrever SQL cru, saber qual é o método HTTP ou o path da rota que o chamou.

## Configuração e segredos

Nenhuma credencial, chave de API ou string de conexão pode estar hardcoded no código fonte. Extraia para variáveis de ambiente, carregadas por um módulo de configuração dedicado (`config/settings.py`, `src/config/index.js`, etc.), que:

- Lê de variáveis de ambiente (`os.environ`, `process.env`) com um valor default seguro apenas para desenvolvimento local, nunca um segredo real como default.
- É o único lugar que outras camadas consultam para obter configuração, em vez de ler `os.environ` espalhado pelo código.
- Nunca é serializado ou devolvido em uma resposta HTTP.

## Tratamento de erros centralizado

Deve existir um único ponto que trata erros não capturados e os transforma em uma resposta HTTP consistente (por exemplo um error handler global do framework, ou um middleware). Controllers e Models podem lançar exceções de domínio específicas; a tradução dessas exceções para status code e corpo de resposta acontece nesse ponto central, não repetida em cada rota.

## Ponto de entrada (composition root)

Deve existir um arquivo claro que monta a aplicação: instancia o framework, registra as rotas, conecta o error handler central e sobe o servidor. Esse arquivo não deve conter regra de negócio nem acesso a dados, apenas a montagem (wiring) das peças.

## Adaptação por linguagem

A estrutura de pastas abaixo é um ponto de partida, não uma regra rígida. Ajuste ao idioma da stack detectada na Fase 1:

**Python/Flask**
```
src/
├── config/
│   └── settings.py
├── models/
│   └── <entidade>_model.py
├── routes/
│   └── <entidade>_routes.py
├── controllers/
│   └── <entidade>_controller.py
├── middlewares/ (ou errors/)
│   └── error_handler.py
└── app.py
```

**Node.js/Express**
```
src/
├── config/
│   └── index.js
├── models/
│   └── <entidade>Model.js
├── routes/
│   └── <entidade>Routes.js
├── controllers/
│   └── <entidade>Controller.js
├── middlewares/
│   └── errorHandler.js
└── app.js
```

Se o projeto já tiver pastas parcialmente organizadas (como `task-manager-api`, que já tem `models/`, `routes/`, `services/`, `utils/`), não recrie a estrutura do zero. Em vez disso:

- Preencha as lacunas (adicione `controllers/` se faltar, adicione `config/` se as credenciais estiverem hardcoded).
- Mova regra de negócio duplicada nas rotas para dentro do Model ou de um novo Controller.
- Conecte serviços que já existem mas nunca são chamados (como um `NotificationService` órfão), ou remova se de fato for código morto sem uso planejado.
- Preserve os nomes de pastas já em uso pelo projeto quando eles já correspondem ao papel correto (não renomeie `services/` para `controllers/` só por convenção, avalie se o conteúdo de fato é um Controller antes de mover).
