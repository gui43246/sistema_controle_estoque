from app.core.database import get_db
from app.core.security.password_hash import hash_password


def create_test_admin(
    drt="900000000",
    name="adm",
    email="adm@text.com",
    phone_number="11991901212"
    ,password="Admteste123"
    
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
                       )VALUES (?,?,?,?,?,?)""",(drt,name,email,phone_number,hash_password(password),"adm"))
        
        return "ok, tudo pronto pra testes"
