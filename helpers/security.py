from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_senha_hash(senha: str):
    return pwd_context.hash(senha)

def verificar_senha(*, senha_recebida: str, hashed_senha: str):
    return pwd_context.verify(senha_recebida, hashed_senha)