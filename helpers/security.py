from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
import os
from dotenv import load_dotenv


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


def get_senha_hash(senha: str):
    """
    Gera um hash seguro para a senha informada.

    Utiliza o algoritmo de hash configurado no `pwd_context` (por padrão, bcrypt) 
    para criar um hash seguro da senha em texto plano.

    :param senha: 
        A senha em texto plano que será convertida para hash.
    
    :return: 
        A senha hasheada.
    
    :rtype: str
    """
    return pwd_context.hash(senha)


def verificar_senha(*, senha_recebida: str, hashed_senha: str):
    """
    Verifica se a senha recebida corresponde ao hash armazenado.

    Compara a senha em texto plano informada pelo usuário com o hash de senha 
    previamente armazenado no banco de dados, garantindo a validação segura.

    :param senha_recebida: 
        A senha em texto plano inserida pelo usuário.
    
    :param hashed_senha: 
        O hash da senha armazenado no banco de dados.
    
    :return: 
        True se a senha for válida, False caso contrário.
    
    :rtype: bool
    """
    return pwd_context.verify(senha_recebida, hashed_senha)


def criar_token_acesso(data: dict, expires_delta: timedelta = None):
    """
    Gera um token JWT de acesso com tempo de expiração.

    Esta função cria e retorna um token JWT assinado utilizando a chave secreta definida, 
    incluindo no payload os dados fornecidos e a data de expiração.

    :param data: 
        Dicionário contendo os dados que devem ser codificados no token. 
        Normalmente inclui informações de identificação, como o `username`.
    
    :param expires_delta: 
        Opcional. Um objeto `timedelta` indicando quanto tempo o token deve ser válido. 
        Se não for informado, será utilizado o tempo padrão definido em `ACCESS_TOKEN_EXPIRE_MINUTES`.
    
    :return: 
        Uma string contendo o token JWT gerado.
    
    :rtype: str
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verificar_token(token: str = Depends(oauth2_scheme)):
    """
    Valida o token JWT de autenticação.

    Esta função decodifica o token JWT utilizando a chave secreta e o algoritmo especificado. 
    Se o token for válido, retorna o `username` extraído do campo `sub` do payload.
    Caso o token seja inválido ou o `username` não seja encontrado, levanta uma exceção HTTP 401.

    :param token: 
        O token JWT enviado na requisição, obtido automaticamente através do `Depends` com o `oauth2_scheme`.
    
    :return: 
        O `username` extraído do payload do token.
    
    :rtype: str

    :raises HTTPException: 
        Se o token for inválido ou não contiver o campo `sub`.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(
            status_code=401,
            detail="Token inválido."
        )
        return username
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )