from app.DATABASE import get_db
from app.security.hash import criar_hash


def criar_adm_text(
    drt="900000000",
    nome="adm",
    email="adm@text.com",
    numero="11991901212"
    ,senha="Admteste123"
    
    ):
    
    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute("""
                       INSERT OR IGNORE INTO users(
                       drt,
                       name,
                       email,
                       numero_telefone
                       ,senha,
                       tipo_user
                       )VALUES (?,?,?,?,?,?)""",(drt,nome,email,numero,criar_hash(senha),"adm"))
        
        return "ok, tudo pronto pra testes"
