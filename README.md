# Sistema de Controle de Estoque

API REST para cadastro e consulta de produtos, controle de quantidades em estoque, registro de movimentações e gerenciamento de usuários. O projeto usa Python, Flask e SQLite, com autenticação JWT e permissões administrativas.

## Funcionalidades

- Cadastro e consulta de produtos por código de barras.
- Consulta do estoque e ajuste de quantidades.
- Histórico de movimentações com usuário, motivo e data.
- Alteração de preço e setor e exclusão de produtos.
- Login e gerenciamento de usuários, incluindo redefinição de senha.
- Senhas armazenadas com hash e limitação de requisições em algumas rotas.

## Requisitos

- Python 3.10 ou superior.
- `pip`.

## Configuração e execução

No Windows PowerShell, a partir da pasta do projeto:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r backend\requirements.txt
```

Configure o arquivo `.env` na raiz do projeto com o caminho do banco e uma chave JWT própria:

```dotenv
CAMINHO_BANCO=banco.db
JWT_SECRET_KEY=troque-por-uma-chave-longa-e-aleatoria
```

O caminho do banco é relativo à pasta `backend/app`. Inicialize as tabelas e os dados padrão:

```powershell
$env:PYTHONPATH = "$PWD\backend"
py -m app.DATABASE
```

> **Atenção:** o comando de inicialização também cria uma conta administrativa de teste (`900000000`, senha `Admteste123`). Ela é apenas para desenvolvimento local: altere ou remova essa conta antes de disponibilizar o sistema. Não use a chave JWT de exemplo em produção.

Inicie a API:

```powershell
py backend\run.py
```

Por padrão, o Flask inicia em `http://127.0.0.1:5000`. O servidor de desenvolvimento está configurado com `debug=True`; use um servidor WSGI e configuração apropriada para produção.

## Autenticação

Envie `POST /login` com `drt` e `senha_digitada`. A resposta inclui um token JWT. Nas rotas protegidas, envie o token no cabeçalho:

```http
Authorization: Bearer <token>
```

Rotas marcadas como administrativas exigem um usuário cujo tipo seja `adm`, `admin`, `user_adm` ou `user_admin`. A conta comum criada pelo cadastro recebe o tipo `user_comum`.

## Endpoints

Todas as rotas estão na raiz da API, sem prefixo `/api`. Os corpos das requisições são JSON.

| Método | Rota | Acesso | Descrição |
|---|---|---|---|
| `POST` | `/login` | Público | Autentica usuário e retorna JWT. |
| `POST` | `/cadastrar` | Administrador | Cadastra produto e inicia quantidade em zero. |
| `POST` | `/consultar` | Autenticado | Consulta produto pelo código de barras. |
| `GET` | `/estoque` | Autenticado | Lista produtos e quantidades. |
| `POST` | `/EditarQuantidade` | Administrador | Define a quantidade e registra ajuste e motivo. |
| `GET` | `/movimentacoes` | Autenticado | Lista o histórico de movimentações. |
| `POST` | `/EditarValor` | Administrador | Altera o preço de um produto. |
| `POST` | `/ajuste_setor_produto` | Administrador | Altera o setor de um produto. |
| `DELETE` | `/produto/<codigo_barras>` | Administrador | Exclui produto sem movimentações associadas. |
| `POST` | `/Cadastro_usuario` | Administrador | Cadastra usuário comum. |
| `GET` | `/usuarios` | Autenticado | Lista usuários sem expor hashes de senha. |
| `POST` | `/reset_senha` | Administrador | Redefine a senha de um usuário. |
| `DELETE` | `/usuarios/<drt>` | Administrador | Exclui usuário sem movimentações e impede autoexclusão. |

### Exemplos

Login:

```json
{
  "drt": "900000000",
  "senha_digitada": "Admteste123"
}
```

Cadastro de produto (com token de administrador):

```json
{
  "codigo_barras": "7891234567890",
  "nome_produto": "Produto de exemplo",
  "valor_prod": 12.5,
  "setor_id": 1
}
```

Consulta de produto:

```json
{
  "codigo_barras": "7891234567890"
}
```

Ajuste de quantidade (o campo `motivo` recebe o ID de um motivo cadastrado):

```json
{
  "codigo_barras": "7891234567890",
  "quantidade": 25,
  "motivo": 4
}
```

## Dados iniciais

A inicialização cria os setores e motivos padrão no SQLite. Os setores começam com IDs de 1 a 8; os motivos são inseridos na ordem abaixo e recebem IDs automaticamente:

1. cadastro de item
2. Compra de produto
3. Devolução
4. Ajuste de estoque
5. Produto danificado
6. Produto vencido
7. Recepção
8. Ruptura
9. exclusão

O arquivo de banco é criado em `backend/app/<CAMINHO_BANCO>`.

## Estrutura do projeto

```text
backend/
├── app/
│   ├── routes/       # Rotas de produtos e usuários
│   ├── services/     # Regras de validação e movimentação
│   ├── security/     # JWT, autorização e hash de senha
│   ├── models/       # Modelo de produto
│   └── DATABASE.py   # Inicialização e acesso ao SQLite
├── tests/            # Arquivos de apoio e requisições REST
└── requirements.txt  # Dependências Python
```

## Testes

Os arquivos em `backend/tests/rest/` são requisições para testar a API manualmente com uma extensão de cliente REST, como REST Client no VS Code. Inicie o servidor e execute primeiro o login para obter o token; as demais requisições protegidas usam esse token.

Para executar os testes automatizados das rotas, na raiz do projeto:

```powershell
$env:PYTHONPATH = "$PWD\backend"
python -m unittest discover -s backend\tests -v
```

Os testes de rota usam um banco SQLite isolado em `backend/tests`, então não alteram o banco de dados da aplicação.
