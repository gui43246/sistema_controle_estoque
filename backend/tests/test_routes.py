"""Testes de requisição das rotas da API usando um banco temporário."""

import itertools
import os
import unittest
from datetime import timedelta
from pathlib import Path

_DATABASE_PATH = Path(__file__).parent / ".route-tests.sqlite3"
_DATABASE_PATH.unlink(missing_ok=True)
os.environ["CAMINHO_BANCO"] = str(_DATABASE_PATH)
os.environ["JWT_SECRET_KEY"] = "chave-de-teste-nao-usar-em-producao"
os.environ["RATELIMIT_STORAGE_URI"] = "memory://"

from flask_jwt_extended import create_access_token

from app import app
from app.DATABASE import criar_adm_text, get_db, init_db
from app.security.hash import criar_hash
from app.services.regmovit import registrar_movimentacao


class TestRotasAPI(unittest.TestCase):
    """Exercita rotas públicas, autenticadas e administrativas."""

    contador_ip = itertools.count(1)
    contador_produto = itertools.count(1)
    contador_usuario = itertools.count(1)
    drt_administrador = "900000000"
    drt_comum = "900000001"
    senha_comum = "Usuario123!"

    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, PROPAGATE_EXCEPTIONS=False)
        init_db()
        criar_adm_text()
        with get_db() as conn:
            conn.execute(
                """INSERT INTO users
                   (drt, name, email, numero_telefone, senha, tipo_user)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    cls.drt_comum,
                    "Usuario Comum",
                    "comum@teste.com",
                    "11912345679",
                    criar_hash(cls.senha_comum),
                    "user_comum",
                ),
            )
        with app.app_context():
            cls.token_admin = create_access_token(identity=cls.drt_administrador)
            cls.token_comum = create_access_token(identity=cls.drt_comum)
            cls.token_expirado = create_access_token(
                identity=cls.drt_administrador,
                expires_delta=timedelta(seconds=-1),
            )
            cls.token_sem_usuario = create_access_token(identity="000000000")
        cls.client = app.test_client()

    def requisicao(
        self, metodo, rota, dados=None, token=None, ip=None, raw=None, content_type=None
    ):
        cabecalhos = {}
        if token:
            cabecalhos["Authorization"] = f"Bearer {token}"
        if dados is not None:
            cabecalhos["Content-Type"] = "application/json"
        if content_type:
            cabecalhos["Content-Type"] = content_type
        numero_ip = next(self.contador_ip)
        endereco = ip or f"10.20.{numero_ip // 250}.{numero_ip % 250 + 1}"
        return self.client.open(
            rota,
            method=metodo,
            json=dados,
            data=raw,
            headers=cabecalhos,
            environ_overrides={"REMOTE_ADDR": endereco},
        )

    def criar_produto(self, codigo=None, movimento=False):
        if codigo is None:
            codigo = f"789{next(self.contador_produto):010d}"
        with get_db() as conn:
            conn.execute(
                """INSERT INTO Produtos_cadastrados
                   (codigo_barras, nome_produto, valor_prod, setor_id)
                   VALUES (?, ?, ?, ?)""",
                (codigo, "Produto de teste", 10.0, 1),
            )
            conn.execute(
                "INSERT INTO estoque (codigo_barras, quantidade) VALUES (?, 0)",
                (codigo,),
            )
        if movimento:
            registrar_movimentacao(
                codigo_barras=codigo,
                quantidade=0,
                status="entrada",
                motivo=1,
                usuario_drt=self.drt_comum,
            )
        return codigo

    def criar_usuario(self, drt=None, movimento=False):
        if drt is None:
            drt = f"8{next(self.contador_usuario):08d}"
        with get_db() as conn:
            conn.execute(
                """INSERT INTO users
                   (drt, name, email, numero_telefone, senha, tipo_user)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    drt,
                    "Usuario Extra",
                    f"usuario{drt}@gmail.com",
                    f"119{int(drt[-8:]):08d}",
                    criar_hash("Usuario123!"),
                    "user_comum",
                ),
            )
        if movimento:
            codigo = self.criar_produto(movimento=True)
            with get_db() as conn:
                conn.execute(
                    "UPDATE movimentacoes SET usuario_drt = ? WHERE codigo_barras = ?",
                    (drt, codigo),
                )
        return drt

    def test_login_valido_invalido_e_corpo_malformado(self):
        resposta = self.requisicao(
            "POST", "/login", raw="{", content_type="application/json"
        )
        self.assertEqual(resposta.status_code, 400)
        casos = [
            (None, 400),
            ([], 400),
            ({"drt": 123, "senha_digitada": "Senha123!"}, 400),
            ({"drt": "", "senha_digitada": "Senha123!"}, 400),
            ({"drt": "000000000", "senha_digitada": "Senha123!"}, 404),
            ({"drt": self.drt_administrador, "senha_digitada": "errada"}, 401),
        ]
        for dados, esperado in casos:
            with self.subTest(dados=dados):
                resposta = self.requisicao("POST", "/login", dados=dados)
                self.assertEqual(resposta.status_code, esperado)

        resposta = self.requisicao(
            "POST",
            "/login",
            dados={"drt": self.drt_administrador, "senha_digitada": "Admteste123"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("token", resposta.get_json())

    def test_rotas_protegidas_rejeitam_token_ausente_invalido_e_usuario_comum(self):
        rotas = [
            ("GET", "/estoque"),
            ("GET", "/movimentacoes"),
            ("GET", "/usuarios"),
            ("POST", "/consultar"),
            ("POST", "/cadastrar"),
            ("POST", "/EditarQuantidade"),
            ("POST", "/EditarValor"),
            ("POST", "/ajuste_setor_produto"),
            ("POST", "/Cadastro_usuario"),
            ("POST", "/reset_senha"),
            ("DELETE", "/produto/inexistente"),
            ("DELETE", "/usuarios/000000000"),
        ]
        for metodo, rota in rotas:
            with self.subTest(metodo=metodo, rota=rota, credencial="ausente"):
                resposta = self.requisicao(metodo, rota)
                self.assertEqual(resposta.status_code, 401)
            with self.subTest(metodo=metodo, rota=rota, credencial="token ruim"):
                resposta = self.requisicao(metodo, rota, token="token-invalido")
                self.assertIn(resposta.status_code, (401, 422))
            with self.subTest(metodo=metodo, rota=rota, credencial="expirado"):
                resposta = self.requisicao(metodo, rota, token=self.token_expirado)
                self.assertIn(resposta.status_code, (401, 422))

        for metodo, rota in rotas:
            if rota in ("/estoque", "/movimentacoes", "/usuarios", "/consultar"):
                continue
            with self.subTest(metodo=metodo, rota=rota, credencial="comum"):
                resposta = self.requisicao(metodo, rota, token=self.token_comum)
                self.assertEqual(resposta.status_code, 403)

        resposta = self.requisicao(
            "POST", "/cadastrar", dados={}, token=self.token_sem_usuario
        )
        self.assertEqual(resposta.status_code, 401)

        codigo = self.criar_produto()
        for metodo, rota, dados in (
            ("GET", "/estoque", None),
            ("GET", "/movimentacoes", None),
            ("GET", "/usuarios", None),
            ("POST", "/consultar", {"codigo_barras": codigo}),
        ):
            with self.subTest(metodo=metodo, rota=rota, credencial="comum autorizado"):
                resposta = self.requisicao(
                    metodo, rota, dados=dados, token=self.token_comum
                )
                self.assertEqual(resposta.status_code, 200)

    def test_rotas_json_rejeitam_corpos_malformados(self):
        rotas = (
            ("POST", "/login", None),
            ("POST", "/consultar", self.token_comum),
            ("POST", "/cadastrar", self.token_admin),
            ("POST", "/EditarQuantidade", self.token_admin),
            ("POST", "/EditarValor", self.token_admin),
            ("POST", "/ajuste_setor_produto", self.token_admin),
            ("POST", "/Cadastro_usuario", self.token_admin),
            ("POST", "/reset_senha", self.token_admin),
        )
        for metodo, rota, token in rotas:
            with self.subTest(rota=rota):
                resposta = self.requisicao(
                    metodo,
                    rota,
                    token=token,
                    raw="{",
                    content_type="application/json",
                )
                self.assertEqual(resposta.status_code, 400)

    def test_cadastro_consulta_e_estoque_de_produtos(self):
        dados = {
            "codigo_barras": "7899000000001",
            "nome_produto": "Arroz",
            "valor_prod": 12.5,
            "setor_id": 1,
        }
        self.assertEqual(
            self.requisicao(
                "POST", "/cadastrar", dados={}, token=self.token_admin
            ).status_code,
            400,
        )
        for invalido in (
            {**dados, "codigo_barras": ""},
            {**dados, "nome_produto": " "},
            {**dados, "valor_prod": True},
            {**dados, "valor_prod": "NaN"},
            {**dados, "valor_prod": "Infinity"},
            {**dados, "setor_id": False},
            {**dados, "setor_id": "abc"},
            {**dados, "setor_id": 1.5},
        ):
            with self.subTest(invalido=invalido):
                resposta = self.requisicao(
                    "POST", "/cadastrar", dados=invalido, token=self.token_admin
                )
                self.assertEqual(resposta.status_code, 422)

        resposta = self.requisicao(
            "POST", "/cadastrar", dados=dados, token=self.token_admin
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_json())
        self.assertEqual(
            self.requisicao(
                "POST", "/cadastrar", dados=dados, token=self.token_admin
            ).status_code,
            409,
        )
        self.assertEqual(
            self.requisicao(
                "POST",
                "/consultar",
                dados={"codigo_barras": ""},
                token=self.token_admin,
            ).status_code,
            422,
        )
        self.assertEqual(
            self.requisicao(
                "POST",
                "/consultar",
                dados={"codigo_barras": "0000000000000"},
                token=self.token_admin,
            ).status_code,
            404,
        )
        consulta = self.requisicao(
            "POST",
            "/consultar",
            dados={"codigo_barras": dados["codigo_barras"]},
            token=self.token_admin,
        )
        self.assertEqual(consulta.status_code, 200)
        self.assertEqual(consulta.get_json()["quantidade"], 0)
        estoque = self.requisicao("GET", "/estoque", token=self.token_admin)
        self.assertEqual(estoque.status_code, 200)
        self.assertTrue(
            any(
                item["codigo_barras"] == dados["codigo_barras"]
                for item in estoque.get_json()
            )
        )
        historico = self.requisicao("GET", "/movimentacoes", token=self.token_admin)
        self.assertEqual(historico.status_code, 200)
        self.assertTrue(
            any(
                item["codigo_barras"] == dados["codigo_barras"]
                for item in historico.get_json()
            )
        )

    def test_ajuste_de_estoque_rejeita_valores_invalidos_e_registra_movimento(self):
        codigo = self.criar_produto()
        base = {"codigo_barras": codigo, "quantidade": 3, "motivo": 2}
        for alteracao in (
            {"quantidade": -1},
            {"quantidade": True},
            {"quantidade": 1.5},
            {"quantidade": "texto"},
            {"motivo": False},
            {"motivo": 1.5},
            {"motivo": 999999},
        ):
            dados = {**base, **alteracao}
            with self.subTest(dados=dados):
                resposta = self.requisicao(
                    "POST", "/EditarQuantidade", dados=dados, token=self.token_admin
                )
                self.assertIn(resposta.status_code, (404, 422))

        consulta_inicial = self.requisicao(
            "POST",
            "/consultar",
            dados={"codigo_barras": codigo},
            token=self.token_admin,
        )
        self.assertEqual(consulta_inicial.get_json()["quantidade"], 0)

        resposta = self.requisicao(
            "POST", "/EditarQuantidade", dados=base, token=self.token_admin
        )
        self.assertEqual(resposta.status_code, 200, resposta.get_json())
        consulta = self.requisicao(
            "POST",
            "/consultar",
            dados={"codigo_barras": codigo},
            token=self.token_admin,
        )
        self.assertEqual(consulta.get_json()["quantidade"], 3)

    def test_alteracao_de_preco_valida_limites_e_produto_inexistente(self):
        codigo = self.criar_produto()
        for valor in (0, -1, True, "NaN", "Infinity", "abc"):
            with self.subTest(valor=valor):
                resposta = self.requisicao(
                    "POST",
                    "/EditarValor",
                    dados={"codigo_barras": codigo, "novo_valor": valor},
                    token=self.token_admin,
                )
                self.assertEqual(resposta.status_code, 422)

        resposta = self.requisicao(
            "POST",
            "/EditarValor",
            dados={"codigo_barras": "0000000000000", "novo_valor": 5},
            token=self.token_admin,
        )
        self.assertEqual(resposta.status_code, 404)
        resposta = self.requisicao(
            "POST",
            "/EditarValor",
            dados={"codigo_barras": codigo, "novo_valor": 15.5},
            token=self.token_admin,
        )
        self.assertEqual(resposta.status_code, 200)

    def test_alteracao_de_setor_valida_entrada_e_existencia(self):
        codigo = self.criar_produto()
        for setor in (-1, 0, 1.5, True, "abc", 999999):
            with self.subTest(setor=setor):
                resposta = self.requisicao(
                    "POST",
                    "/ajuste_setor_produto",
                    dados={"codigo_barras": codigo, "novo_setor": setor},
                    token=self.token_admin,
                )
                self.assertIn(resposta.status_code, (404, 422))
        resposta = self.requisicao(
            "POST",
            "/ajuste_setor_produto",
            dados={"codigo_barras": "0000000000000", "novo_setor": 2},
            token=self.token_admin,
        )
        self.assertEqual(resposta.status_code, 404)
        resposta = self.requisicao(
            "POST",
            "/ajuste_setor_produto",
            dados={"codigo_barras": codigo, "novo_setor": 2},
            token=self.token_admin,
        )
        self.assertEqual(resposta.status_code, 200)

    def test_exclusao_de_produto_preserva_historico(self):
        self.assertEqual(
            self.requisicao(
                "DELETE", "/produto/inexistente", token=self.token_admin
            ).status_code,
            404,
        )
        codigo_com_historico = self.criar_produto(movimento=True)
        resposta = self.requisicao(
            "DELETE", f"/produto/{codigo_com_historico}", token=self.token_admin
        )
        self.assertEqual(resposta.status_code, 409)
        codigo_limpo = self.criar_produto()
        resposta = self.requisicao(
            "DELETE", f"/produto/{codigo_limpo}", token=self.token_admin
        )
        self.assertEqual(resposta.status_code, 200)

    def test_cadastro_listagem_reset_e_exclusao_de_usuarios(self):
        dados = {
            "DRT": "812345678",
            "name": "Maria Silva",
            "Email": "maria@gmail.com",
            "numero_tel": "11912345678",
            "senha": "SenhaForte123!",
        }
        self.assertEqual(
            self.requisicao(
                "POST", "/Cadastro_usuario", dados={}, token=self.token_admin
            ).status_code,
            400,
        )
        casos_invalidos = (
            {**dados, "DRT": "abc"},
            {**dados, "name": "Maria123"},
            {**dados, "Email": "maria@dominio-invalido.org"},
            {**dados, "numero_tel": "123"},
            {**dados, "senha": "fraca"},
            {**dados, "name": None},
        )
        for invalido in casos_invalidos:
            with self.subTest(invalido=invalido):
                resposta = self.requisicao(
                    "POST", "/Cadastro_usuario", dados=invalido, token=self.token_admin
                )
                self.assertIn(resposta.status_code, (400, 409))

        resposta = self.requisicao(
            "POST", "/Cadastro_usuario", dados=dados, token=self.token_admin
        )
        self.assertEqual(resposta.status_code, 201, resposta.get_json())
        self.assertEqual(
            self.requisicao(
                "POST", "/Cadastro_usuario", dados=dados, token=self.token_admin
            ).status_code,
            409,
        )
        email_duplicado = {
            **dados,
            "DRT": "812345679",
            "numero_tel": "11912345670",
        }
        resposta = self.requisicao(
            "POST", "/Cadastro_usuario", dados=email_duplicado, token=self.token_admin
        )
        self.assertEqual(resposta.status_code, 409)
        telefone_duplicado = {
            **dados,
            "DRT": "812345670",
            "Email": "outro@gmail.com",
        }
        resposta = self.requisicao(
            "POST",
            "/Cadastro_usuario",
            dados=telefone_duplicado,
            token=self.token_admin,
        )
        self.assertEqual(resposta.status_code, 409)
        usuarios = self.requisicao("GET", "/usuarios", token=self.token_admin)
        self.assertEqual(usuarios.status_code, 200)
        usuario = next(
            item for item in usuarios.get_json() if item["drt"] == dados["DRT"]
        )
        self.assertNotIn("senha", usuario)

        reset_invalido = {
            "DRT": dados["DRT"],
            "nova_senha": "OutraForte123!",
            "confirmar_senha": "diferente",
        }
        self.assertEqual(
            self.requisicao(
                "POST", "/reset_senha", dados=reset_invalido, token=self.token_admin
            ).status_code,
            400,
        )
        reset_usuario_ausente = {
            "DRT": "000000000",
            "nova_senha": "OutraForte123!",
            "confirmar_senha": "OutraForte123!",
        }
        self.assertEqual(
            self.requisicao(
                "POST",
                "/reset_senha",
                dados=reset_usuario_ausente,
                token=self.token_admin,
            ).status_code,
            404,
        )
        reset = {**reset_invalido, "confirmar_senha": "OutraForte123!"}
        self.assertEqual(
            self.requisicao(
                "POST", "/reset_senha", dados=reset, token=self.token_admin
            ).status_code,
            200,
        )
        login = self.requisicao(
            "POST",
            "/login",
            dados={"drt": dados["DRT"], "senha_digitada": "OutraForte123!"},
        )
        self.assertEqual(login.status_code, 200)

        self.assertEqual(
            self.requisicao(
                "DELETE", f"/usuarios/{self.drt_administrador}", token=self.token_admin
            ).status_code,
            409,
        )
        self.assertEqual(
            self.requisicao(
                "DELETE", "/usuarios/000000000", token=self.token_admin
            ).status_code,
            404,
        )
        drt_com_historico = self.criar_usuario(movimento=True)
        self.assertEqual(
            self.requisicao(
                "DELETE", f"/usuarios/{drt_com_historico}", token=self.token_admin
            ).status_code,
            409,
        )
        drt_limpo = self.criar_usuario()
        self.assertEqual(
            self.requisicao(
                "DELETE", f"/usuarios/{drt_limpo}", token=self.token_admin
            ).status_code,
            200,
        )

    def test_limite_de_tentativas_de_login(self):
        ip = "192.0.2.200"
        for tentativa in range(5):
            resposta = self.requisicao(
                "POST",
                "/login",
                dados={"drt": "000000000", "senha_digitada": "errada"},
                ip=ip,
            )
            self.assertEqual(resposta.status_code, 404, f"tentativa {tentativa + 1}")
        resposta = self.requisicao(
            "POST",
            "/login",
            dados={"drt": "000000000", "senha_digitada": "errada"},
            ip=ip,
        )
        self.assertEqual(resposta.status_code, 429)


if __name__ == "__main__":
    unittest.main()
