from fastapi import Depends, FastAPI, HTTPException, APIRouter, Query
from fastapi.responses import JSONResponse 
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from database import get_session
from models import Client
from helpers.security import get_senha_hash, verificar_senha
from helpers.validacao import verificar_campos_obrigatorios

router = APIRouter()

@router.get("/")
def listar_clientes(
    nome: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session)
):
    
    query = select(Client).where(Client.deleted == False)
    if nome:
        query = query.where(Client.nome.ilike(f"%{nome}%"))

    if email:
        query = query.where(Client.email.ilike(f"%{email}%"))

    query = query.limit(limit).offset(offset)

    db_clients = session.scalars(query).all()

    if len(db_clients) == 0:
        raise HTTPException(
                status_code=404,
                detail='Clientes não encontrados com os parametros solicitados!',
            )
    clientes = [
        {
            "id": client.id,
            "nome": client.nome,
            "email": client.email,
            "cpf": client.cpf
        }
        for client in db_clients
    ]
    
    data = {
        "mensagem": "Clientes encontrados com sucesso",
        "total": len(clientes),
        "clientes": clientes
    }
    
    return JSONResponse(content=data, status_code=200)

@router.get("/{id}")
def teste_de_get(id: int, session: Session = Depends(get_session)):
    db_client = session.scalar(
        select(Client).where(
            (Client.id == id) & (Client.deleted == False)
        )
    )
    if not db_client:
        raise HTTPException(
                status_code=404,
                detail='Cliente não encontrado!',
            )
    
    data = {
        "mensagem": "Cliente encontrado com sucesso",
        "cliente": {
                "id": db_client.id,
                "email": db_client.email,
                "cpf": db_client.cpf,
                "nome": db_client.nome
            }
    }
    return JSONResponse(content=data, status_code=200)

@router.post("/")
def teste_de_get(body: dict, session: Session = Depends(get_session)):
    obrigatorios = ["email", "cpf", "nome"]
    validacao = verificar_campos_obrigatorios(obrigatorios=obrigatorios, body=body)
    if not validacao:
        raise HTTPException(
            status_code=400,
            detail='Informação obrigatória para cadastro não informada',
        )
    cpf = body["cpf"].replace("-", ".").replace(".", "")
    db_client = session.scalar(
        select(Client).where(
            ((Client.email == body["email"]) | (Client.cpf == cpf)) & (Client.deleted == False)
        )
    )
    if db_client:
        raise HTTPException(
                status_code=409,
                detail='Cliente com essas informações já cadastrado!',
            )
    
    db_client = Client(
        email=body['email'],
        cpf=cpf,
        nome=body["nome"]
    )
    session.add(db_client)
    session.commit()
    session.refresh(db_client)

    data = {
        "mensagem": "Cliente cadastrado com sucesso",
        "cliente": {
                "id": db_client.id,
                "email": db_client.email,
                "cpf": cpf,
                "nome": db_client.nome,
            }
    }
    return JSONResponse(content=data, status_code=200)

@router.put("/{id}")
def teste_de_get(id: int, body: dict, session: Session = Depends(get_session)):
    db_client = session.scalar(
        select(Client).where(
            (Client.id == id) & (Client.deleted == False)
        )
    )
    if not db_client:
        raise HTTPException(
                status_code=404,
                detail='Cliente não encontrado!',
            )
    
    if body.get("cpf"):
        cpf = body["cpf"].replace("-", ".").replace(".", "")
        db_client_validacao = session.scalar(
        select(Client).where(
            (Client.cpf == cpf) & (Client.deleted == False) & (Client.id != id)
        ))
        if db_client_validacao:
            raise HTTPException(
                    status_code=409,
                    detail='Cliente com essas informações já cadastrado!',
                )
        db_client.cpf = body["cpf"].replace("-", ".").replace(".", "")

    if body.get("email"):
        db_client_validacao = session.scalar(
        select(Client).where(
            (Client.email == body["email"]) & (Client.deleted == False) & (Client.id != id)
        ))
        if db_client_validacao:
            raise HTTPException(
                    status_code=409,
                    detail='Cliente com essas informações já cadastrado!',
                )
        db_client.email = body["email"]
    
    if body.get("nome"):
        db_client.nome = body["nome"]
    
    session.commit()
    session.refresh(db_client)

    data = {
        "mensagem": "Cliente alterado com sucesso",
        "cliente": {
                "id": db_client.id,
                "email": db_client.email,
                "cpf": db_client.cpf,
                "nome": db_client.nome
            }
    }
    return JSONResponse(content=data, status_code=200)

@router.delete("/{id}")
def teste_de_get(id: int, session: Session = Depends(get_session)):
    db_client = session.scalar(
        select(Client).where(
            (Client.id == id) & (Client.deleted == False)
        )
    )
    if not db_client:
        raise HTTPException(
                status_code=404,
                detail='Cliente não encontrado!',
            )
    
    db_client.deleted = True
    session.commit()
    session.refresh(db_client)

    data = {
        "mensagem": "Cliente deletado com sucesso",
        "cliente": {
                "id": db_client.id,
                "email": db_client.email,
                "cpf": db_client.cpf,
                "nome": db_client.nome,
            }
    }
    return JSONResponse(content=data, status_code=200)