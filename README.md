# Sistema de controle de estoque

Este projeto é uma API para controlar produtos, quantidades em estoque e movimentações. Também permite cadastrar usuários e controlar o acesso às operações.

A API foi feita em Python com Flask. Os dados ficam em um banco SQLite. As rotas protegidas usam token JWT.

## O que a aplicação faz

- Cadastra produtos e cria o registro inicial de estoque.
- Consulta produtos ativos e lista o estoque.
- Altera quantidade, preço e setor de produtos.
- Registra movimentações de entrada, ajuste e exclusão.
- Cadastra, lista, redefine a senha e exclui usuários conforme as permissões.

## Requisitos

- Python 3.10 ou superior.
- `pip`.

Os comandos abaixo foram escritos para PowerShell e devem ser executados na pasta raiz do projeto.

## Preparar o ambiente

Crie e ative um ambiente virtual e instale as dependências:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r backend\requirements.txt
```

Gere uma chave JWT aleatória com o comando abaixo e copie o valor exibido para
`JWT_SECRET_KEY` no arquivo `.env` da raiz do projeto:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

O arquivo `.env` deve conter:

```dotenv
CAMINHO_BANCO=banco.db
JWT_SECRET_KEY=<valor gerado pelo comando>
```

O caminho de `CAMINHO_BANCO` é relativo à pasta `backend/app`. Com o valor `banco.db`, o arquivo será criado em `backend/app/banco.db`.

## Criar o banco e os dados iniciais

Ainda na pasta raiz, configure o caminho de importação e execute a inicialização:

```powershell
$env:PYTHONPATH = "$PWD\backend"
py -m app.core.database
```

Esse comando cria as tabelas, os setores e os motivos. Também cria uma conta administrativa local para facilitar testes manuais:

- DRT: `900000000`
- Senha: `Admteste123`

Essa conta é somente para desenvolvimento. Troque a senha ou remova a conta antes de disponibilizar a aplicação para outras pessoas.

## Iniciar a API em desenvolvimento

Na pasta raiz, com o ambiente virtual ativo e o arquivo `.env` configurado, execute:

```powershell
py backend\run.py
```

A API ficará disponível em `http://127.0.0.1:5000`. O modo de depuração fica desligado por padrão. Para habilitá-lo explicitamente durante o desenvolvimento, defina `FLASK_DEBUG=1` antes de iniciar.

## Executar em produção

Instale as dependências de `backend/requirements.txt`, configure `JWT_SECRET_KEY` com uma chave aleatória forte e inicie o servidor WSGI Waitress a partir da pasta raiz:

```powershell
$env:PYTHONPATH = "$PWD\backend"
$env:FLASK_ENV = "production"
$env:FLASK_DEBUG = "0"
waitress-serve --listen=0.0.0.0:5000 app:app
```

O Waitress atende a aplicação WSGI sem ativar o servidor de desenvolvimento do Flask. Debug ativo em produção é recusado.

O limitador de requisições usa `memory://` por padrão. Esse armazenamento mantém os contadores apenas no processo atual; processos ou instâncias diferentes têm contadores independentes. Para compartilhar limites entre instâncias, configure `RATELIMIT_STORAGE_URI` com um armazenamento externo compatível, como Redis.

## Autenticação e permissões

Para entrar, envie `POST /login` com o DRT e a senha. Se as credenciais estiverem corretas, a resposta inclui um token:

```json
{
  "drt": "900000000",
  "senha_digitada": "Admteste123"
}
```

Envie o token nas rotas protegidas usando o cabeçalho:

```http
Authorization: Bearer <token>
```

O token de acesso tem validade padrão de 60 minutos, configurável pela variável `JWT_ACCESS_MINUTES`. Rotas administrativas aceitam os tipos `adm`, `admin`, `user_adm` e `user_admin`. Usuários cadastrados pela API recebem o tipo `user_comum`.

## Rotas disponíveis

Todas as rotas ficam na raiz do endereço, sem prefixo `/api`. As requisições com dados devem enviar JSON.

| Método | Rota | Acesso | Uso |
|---|---|---|---|
| `POST` | `/login` | Público | Confere DRT e senha e retorna um token. |
| `POST` | `/cadastrar` | Administrador | Cadastra produto e cria estoque inicial zerado. |
| `POST` | `/consultar` | Usuário autenticado | Consulta um produto ativo pelo código de barras. |
| `GET` | `/estoque` | Usuário autenticado | Lista produtos ativos e suas quantidades. |
| `POST` | `/EditarQuantidade` | Administrador | Define a quantidade em estoque e registra o motivo. |
| `GET` | `/movimentacoes` | Usuário autenticado | Consulta o histórico de movimentações. |
| `POST` | `/EditarValor` | Administrador | Altera o preço de um produto ativo. |
| `POST` | `/ajuste_setor_produto` | Administrador | Altera o setor de um produto ativo. |
| `PUT` | `/ExcluirProduto` | Administrador | Exclui logicamente um produto e zera seu estoque. |
| `POST` | `/Cadastro_usuario` | Administrador | Cadastra um usuário comum. |
| `GET` | `/usuarios` | Administrador | Lista usuários sem retornar hashes de senha. |
| `POST` | `/reset_senha` | Administrador | Redefine a senha de um usuário. |
| `DELETE` | `/usuarios/<drt>` | Administrador | Exclui usuário sem movimentações e impede autoexclusão. |

As listagens `GET /estoque`, `GET /movimentacoes` e `GET /usuarios` aceitam os
parâmetros `page` (padrão `1`) e `per_page` (padrão `50`, máximo `200`). A
resposta contém os registros da página em `items`, a página atual em `page`, o
tamanho solicitado em `per_page` e a quantidade total de registros em `total`.
Uma página inválida retorna HTTP 400.

Exemplo de resposta de `GET /estoque?page=1&per_page=2`:

```json
{
  "items": [
    {
      "codigo_barras": "789000000001",
      "nome_produto": "Produto exemplo",
      "valor_prod": 12.5,
      "setor_id": 1,
      "quantidade": 8
    },
    {
      "codigo_barras": "789000000002",
      "nome_produto": "Outro produto",
      "valor_prod": 7.9,
      "setor_id": 2,
      "quantidade": 3
    }
  ],
  "page": 1,
  "per_page": 2,
  "total": 18
}
```

### Exemplos de requisição

Os exemplos abaixo mostram o corpo esperado. Para rotas protegidas, inclua também o cabeçalho `Authorization` com o token obtido no login.

#### Cadastrar produto

`setor_id` precisa corresponder a um setor existente. O produto é criado com quantidade zero.

```http
POST /cadastrar
Content-Type: application/json

{
  "codigo_barras": "7891234567890",
  "nome_produto": "Produto de exemplo",
  "valor_prod": 12.5,
  "setor_id": 1
}
```

#### Consultar produto

```http
POST /consultar
Content-Type: application/json

{
  "codigo_barras": "7891234567890"
}
```

#### Ajustar estoque

O campo `motivo` é opcional. Quando não for enviado, a API usa o motivo de ajuste de estoque (ID 4). Os motivos aceitos por esta rota são devolução (3), ajuste de estoque (4), produto danificado (6), produto vencido (7) e ruptura (9).

```http
POST /EditarQuantidade
Content-Type: application/json

{
  "codigo_barras": "7891234567890",
  "quantidade": 25,
  "motivo": 4
}
```

#### Alterar preço

```http
POST /EditarValor
Content-Type: application/json

{
  "codigo_barras": "7891234567890",
  "novo_valor": 14.9
}
```

#### Alterar setor

`novo_setor` deve ser o ID de um setor existente.

```http
POST /ajuste_setor_produto
Content-Type: application/json

{
  "codigo_barras": "7891234567890",
  "novo_setor": 2
}
```

#### Excluir produto

A exclusão é lógica: o produto permanece no banco com status `excluido`, deixa de aparecer nas consultas de produtos ativos e tem o estoque zerado. O motivo de exclusão é definido pela API; não envie `motivo` no corpo.

```http
PUT /ExcluirProduto
Content-Type: application/json

{
  "codigo_barras": "7891234567890"
}
```

## Dados iniciais do banco

A inicialização cadastra oito setores e onze motivos. Os IDs são criados na ordem abaixo:

| ID | Motivo |
|---:|---|
| 1 | cadastro de item |
| 2 | Compra de produto |
| 3 | Devolução |
| 4 | Ajuste de estoque |
| 5 | valor ajustado |
| 6 | Produto danificado |
| 7 | Produto vencido |
| 8 | Recepção |
| 9 | Ruptura |
| 10 | exclusão |
| 11 | Venda |

As rotas de preço e exclusão usam motivos definidos no servidor. A rota de ajuste de estoque aceita apenas os IDs indicados no exemplo acima.

## Executar os testes

Execute a suíte a partir da pasta raiz do projeto:

```powershell
py -m pytest -v --basetemp=.pytest-tmp
```

O arquivo `pytest.ini` adiciona `backend` ao caminho de importação do pytest, permitindo que os testes encontrem os módulos `app`. Os testes automatizados usam bancos temporários; não é necessário apontar os testes para o banco de desenvolvimento.

Os arquivos `.rest` em `tests/rest` são exemplos para executar requisições manualmente em uma extensão de cliente REST. Eles não fazem parte da suíte automática.

## Organização das pastas

```text
backend/
├── app/
│   ├── core/       # Configuração do banco e segurança
│   ├── models/     # Modelos de produto, usuário e movimentação
│   ├── products/   # Rotas e serviços de produtos e estoque
│   ├── users/      # Rotas e validações de usuários
│   └── utils/      # Utilitários da aplicação
├── requirements.txt
└── run.py
tests/
├── rest/           # Exemplos de requisições manuais
└── test_*.py       # Testes automatizados
```
