from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import select

from database import get_session
from models import User
from helpers.security import get_senha_hash, verificar_senha
from helpers.validacao import verificar_campos_obrigatorios

router = APIRouter()

@router.post("/login")
def teste_de_get(body: dict, session: Session = Depends(get_session)):
    obrigatorios = ["username", "senha"]
    validacao = verificar_campos_obrigatorios(obrigatorios=obrigatorios, body=body)
    if not validacao:
        raise HTTPException(
            status_code=400,
            detail='Informação obrigatória para login não informada',
        )
    db_user = session.scalar(
        select(User).where(
            (User.username == body["username"]) & (User.deleted == False)
        )
    )
    if not db_user:
        raise HTTPException(
                status_code=404,
                detail='Usuário com essas informações não encontrado!',
            )
    if not verificar_senha(senha_recebida=body["senha"], hashed_senha=db_user.senha):
        raise HTTPException(
                status_code=400,
                detail='Senha inserida está incorreta!',
            )
    
    return {"Mensagem": "ta certo!"}

@router.post("/register")
def teste_de_get(body: dict, session: Session = Depends(get_session)):
    obrigatorios = ["username", "email", "senha"]
    validacao = verificar_campos_obrigatorios(obrigatorios=obrigatorios, body=body)
    if not validacao:
        raise HTTPException(
            status_code=400,
            detail='Informação obrigatória para cadastro não informada',
        )
    
    db_user = session.scalar(
        select(User).where(
            ((User.username == body["username"]) | (User.email == body["email"])) & (User.deleted == False)
        )
    )
    if db_user:
        raise HTTPException(
                status_code=409,
                detail='Usuário com essas informações já cadastrado!',
            )
    
    db_user = User(
    username=body['username'],
    senha=get_senha_hash(body['senha']),
    email=body['email']
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    data = {
        "mensagem": "Usuario cadastrado com sucesso",
        "usuario": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email
            }
    }
    return JSONResponse(content=data, status_code=200)