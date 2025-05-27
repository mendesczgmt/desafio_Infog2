from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import timedelta
from jose import JWTError, jwt


from database import get_session
from models import User
from helpers.security import (
    get_senha_hash, verificar_senha,
    criar_token_acesso,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme)
from helpers.validacao import verificar_campos_obrigatorios

router = APIRouter()


@router.post("/login")
def realizar_login(body: dict, session: Session = Depends(get_session)):
    """
    Realiza o login de um usuário.

    Parâmetros:
    - body (dict): Contém 'username' e 'senha'.
    - session (Session): Sessão do banco de dados.

    Retorna:
    - JSONResponse com status e mensagem de sucesso.
    - HTTP 400 se faltar campos ou a senha estiver incorreta.
    - HTTP 404 se o usuário não for encontrado.
    """
    obrigatorios = ["username", "senha"]
    validacao = verificar_campos_obrigatorios(obrigatorios=obrigatorios, body=body)

    if not validacao:
        raise HTTPException(
            status_code=400,
            detail="Informação obrigatória para login não informada."
        )

    db_user = session.scalar(
        select(User).where(
            (User.username == body["username"]) & (User.deleted == False)
        )
    )

    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="Usuário com essas informações não encontrado!"
        )

    if not verificar_senha(senha_recebida=body["senha"], hashed_senha=db_user.senha):
        raise HTTPException(
            status_code=400,
            detail="Senha inserida está incorreta!"
        )

    access_token = criar_token_acesso(
        data={"sub": db_user.username}
    )

    response = {
        "status": "success",
        "message": "Login realizado com sucesso!",
        "access_token": access_token,
        "token_type": "bearer"
    }

    return JSONResponse(content=response, status_code=200)


@router.post("/register")
def registrar_usuario(body: dict, session: Session = Depends(get_session)):
    """
    Realiza o cadastro de um novo usuário.

    Parâmetros:
    - body (dict): Contém 'username', 'email' e 'senha'.
    - session (Session): Sessão do banco de dados.

    Retorna:
    - JSONResponse com status, mensagem e dados do usuário cadastrado.
    - HTTP 400 se faltar campos obrigatórios.
    - HTTP 409 se o usuário já existir.
    """
    obrigatorios = ["username", "email", "senha"]
    validacao = verificar_campos_obrigatorios(obrigatorios=obrigatorios, body=body)

    if not validacao:
        raise HTTPException(
            status_code=400,
            detail="Informação obrigatória para cadastro não informada."
        )

    db_user = session.scalar(
        select(User).where(
            ((User.username == body["username"]) | (User.email == body["email"])) & (User.deleted == False)
        )
    )

    if db_user:
        raise HTTPException(
            status_code=409,
            detail="Usuário com essas informações já cadastrado!"
        )

    db_user = User(
        username=body["username"],
        senha=get_senha_hash(body["senha"]),
        email=body["email"]
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    response = {
        "status": "success",
        "message": "Usuário cadastrado com sucesso.",
        "usuario": {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email
        }
    }

    return JSONResponse(content=response, status_code=200)


@router.post("/refresh-token")
def refresh_token(refresh_token: str = Depends(oauth2_scheme)):
    """
    Endpoint para gerar um novo access token a partir de um refresh token válido.
    
    Args:
        refresh_token (str): Token JWT de refresh.
    
    Returns:
        dict: Novo token de acesso (access token) e o token de refresh (opcional).
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401,
                detail="Refresh token inválido"
            )
        
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Refresh token inválido"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = criar_token_acesso(
        data={"sub": username},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }