# Sistema de Controle de Estoque

API REST para cadastro e consulta de produtos, controle de estoque, registro de movimentações e gerenciamento de usuários. O projeto usa Python, Flask, SQLite, autenticação JWT e permissões administrativas.

## Requisitos

- Python 3.10 ou superior.
- `pip`.

## Configuração

No diretório raiz do projeto, crie um arquivo `.env`:

```dotenv
CAMINHO_BANCO=banco.db
JWT_SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
```

`CAMINHO_BANCO` é relativo a `backend/app`. O banco será criado em `backend/app/banco.db`.

### Instalação e inicialização pelo CMD

```cmd
rem Execute estes comandos a partir da pasta raiz do projeto
py -m venv .venv
.venv\Scripts\activate.bat
py -m pip install -r backend\requirements.txt
set PYTHONPATH=%CD%\backend
py -m app.core.database
```

A inicialização cria as tabelas, os setores e os motivos padrão, além de uma conta administrativa local para testes:

- DRT: `900000000`
- Senha: `Admteste123`

Use essa conta somente em desenvolvimento. Troque a senha ou remova a conta antes de disponibilizar o sistema.

### Iniciar a API

Com o ambiente virtual ativado, na raiz do projeto:

```cmd
py backend\run.py
```

A API inicia em `http://127.0.0.1:5000`. O servidor embutido do Flask está configurado em modo de depuração e deve ser usado apenas localmente.

## Autenticação

Envie `POST /login` com `drt` e `senha_digitada`. A resposta inclui um token JWT. Para rotas protegidas, envie:

```http
Authorization: Bearer <token>
```

As rotas administrativas aceitam usuários com tipo `adm`, `admin`, `user_adm` ou `user_admin`. Usuários cadastrados pela rota recebem o tipo `user_comum`.

## Endpoints

Todas as rotas ficam na raiz da API, sem prefixo `/api`. Os corpos das requisições são JSON.

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `POST` | `/login` | Público | Autentica usuário e retorna JWT. |
| `POST` | `/cadastrar` | Administrador | Cadastra produto com estoque inicial zero. |
| `POST` | `/consultar` | Autenticado | Consulta produto pelo código de barras. |
| `GET` | `/estoque` | Autenticado | Lista produtos ativos e seus saldos. |
| `POST` | `/EditarQuantidade` | Administrador | Define quantidade e registra o motivo. |
| `GET` | `/movimentacoes` | Autenticado | Lista o histórico de movimentações. |
| `POST` | `/EditarValor` | Administrador | Altera o preço de um produto. |
| `POST` | `/ajuste_setor_produto` | Administrador | Altera o setor de um produto. |
| `PUT` | `/ExcluirProduto` | Administrador | Marca o produto como excluído e registra o motivo. |
| `POST` | `/Cadastro_usuario` | Administrador | Cadastra usuário comum. |
| `GET` | `/usuarios` | Autenticado | Lista usuários sem expor hashes de senha. |
| `POST` | `/reset_senha` | Administrador | Redefine a senha de um usuário. |
| `DELETE` | `/usuarios/<drt>` | Administrador | Exclui usuário sem movimentações e impede autoexclusão. |

### Exemplos de requisição

Cadastro de produto (requer token de administrador):

```http
POST /cadastrar
Content-Type: application/json
Authorization: Bearer <token>

{
  "codigo_barras": "7891234567890",
  "nome_produto": "Produto de exemplo",
  "valor_prod": 12.5,
  "setor_id": 1
}
```

Ajuste de quantidade. `motivo` recebe o ID de um motivo cadastrado:

```json
{
  "codigo_barras": "7891234567890",
  "quantidade": 25,
  "motivo": 4
}
```

Exclusão lógica de produto. O registro permanece no banco com status `excluido`; ele deixa de aparecer na consulta e na listagem de estoque:

```http
PUT /ExcluirProduto
Content-Type: application/json
Authorization: Bearer <token>

{
  "codigo_barras": "7891234567890",
  "motivo": 9
}
```

## Dados iniciais

A inicialização cria oito setores e nove motivos. Os IDs dos motivos são inseridos nesta ordem:

1. cadastro de item
2. Compra de produto
3. Devolução
4. Ajuste de estoque
5. Produto danificado
6. Produto vencido
7. Recepção
8. Ruptura
9. exclusão

## Estrutura do projeto

```text
backend/
├── app/
│   ├── core/           # Banco de dados e segurança
│   ├── models/         # Produtos, usuários e movimentações
│   ├── products/       # Rotas e serviços de produtos/estoque
│   ├── users/          # Rotas e validações de usuários
│   └── utils/          # Logger
├── requirements.txt
└── run.py
tests/
├── rest/               # Requisições manuais para cliente REST
└── test_*.py           # Testes automatizados
```

## Testes e logs

Instale as dependências e execute os testes automatizados a partir da raiz:

```cmd
py -m pytest
```

Os arquivos `.rest` em `tests/rest` contêm exemplos para enviar individualmente por um cliente REST. O servidor Flask mostra as requisições recebidas no console. O utilitário em `backend/app/utils/logger.py` grava mensagens quando chamado; os testes automatizados usam esse logger para registrar seus resultados em `logs/app.log`.

Para direcionar o logger a outro arquivo, defina `ESTOQUE_LOG_FILE` antes de iniciar os testes.
