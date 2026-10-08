"""Verifica o formato e a unicidade da identificação DRT de um usuário."""

from app.DATABASE import get_db
import re 
def validar_DRT(drt=str)-> tuple[bool,str]:

    
    """Verifica se a DRT tem nove dígitos e ainda não está cadastrada."""
    if not isinstance(drt,str):
        return False, "campo invalido"
    
    if len(drt)!=9 or  not re.fullmatch(r"\d+",drt):
        return False, "Verifique a DRT"
    
    with get_db() as conn:
        cursor=conn.cursor()
        cursor.execute("""SELECT drt FROM users 
                       WHERE drt = ? """,(drt,))
        resultado=cursor.fetchall()
        if resultado:
            return False , "DRT ja cadastrada "
        
        
    return True, "ok"

