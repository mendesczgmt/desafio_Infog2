from fastapi import Depends, HTTPException, APIRouter, Query
from fastapi.responses import JSONResponse 
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from database import get_session
from models import Client
from helpers.validacao import verificar_campos_obrigatorios

router = APIRouter()


@router.get("/")
def buscar_clientes(
    nome: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session)
):
    """
    Busca uma lista de clientes com filtros opcionais.

    Parâmetros:
    - nome (str, opcional): Filtro parcial pelo nome do cliente.
    - email (str, opcional): Filtro parcial pelo e-mail do cliente.
    - limit (int, padrão=10): Quantidade máxima de registros retornados.
    - offset (int, padrão=0): Ponto de partida para a busca.
    - session (Session): Sessão do banco de dados (injeção de dependência).

    Retorna:
    - JSONResponse com status, mensagem, quantidade total e lista de clientes.
    - HTTP 404 se nenhum cliente for encontrado.
    """
    
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
            detail="Clientes não encontrados com os parâmetros solicitados!"
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
    
    response = {
        "status": "success",
        "message": "Clientes encontrados com sucesso.",
        "total": len(clientes),
        "clientes": clientes
    }
    
    return JSONResponse(content=response, status_code=200)


@router.get("/{id}")
def buscar_cliente_por_id(id: int, session: Session = Depends(get_session)):
    """
    Busca um cliente pelo ID.

    Parâmetros:
    - id (int): ID do cliente a ser buscado.
    - session (Session): Sessão do banco de dados (injeção de dependência).

    Retorna:
    - JSONResponse com status, mensagem e dados do cliente.
    - HTTP 404 se o cliente não for encontrado.
    """
    db_client = session.scalar(
        select(Client).where(
            (Client.id == id) & (Client.deleted == False)
        )
    )
    
    if not db_client:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado!"
        )
    
    response = {
        "status": "success",
        "message": "Cliente encontrado com sucesso.",
        "cliente": {
            "id": db_client.id,
            "email": db_client.email,
            "cpf": db_client.cpf,
            "nome": db_client.nome
        }
    }
    
    return JSONResponse(content=response, status_code=200)


@router.post("/")
def criar_cliente(body: dict, session: Session = Depends(get_session)):
    """
    Cria um novo cliente, validando campos obrigatórios e duplicidade.

    Parâmetros:
    - body (dict): Dados do cliente contendo 'email', 'cpf' e 'nome'.
    - session (Session): Sessão do banco de dados (injeção de dependência).

    Retorna:
    - JSONResponse com status, mensagem e dados do cliente criado.
    - HTTP 400 se faltar campos obrigatórios.
    - HTTP 409 se cliente já estiver cadastrado.
    """
    obrigatorios = ["email", "cpf", "nome"]
    validacao = verificar_campos_obrigatorios(obrigatorios=obrigatorios, body=body)
    
    if not validacao:
        raise HTTPException(
            status_code=400,
            detail="Informação obrigatória para cadastro não informada."
        )
    
    cpf = body["cpf"].replace("-", "").replace(".", "")
    
    db_client = session.scalar(
        select(Client).where(
            ((Client.email == body["email"]) | (Client.cpf == cpf)) & (Client.deleted == False)
        )
    )
    
    if db_client:
        raise HTTPException(
            status_code=409,
            detail="Cliente com essas informações já cadastrado!"
        )
    
    db_client = Client(
        email=body["email"],
        cpf=cpf,
        nome=body["nome"]
    )
    
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    
    response = {
        "status": "success",
        "message": "Cliente cadastrado com sucesso.",
        "cliente": {
            "id": db_client.id,
            "email": db_client.email,
            "cpf": cpf,
            "nome": db_client.nome
        }
    }
    
    return JSONResponse(content=response, status_code=201)


@router.put("/{id}")
def atualizar_cliente(id: int, body: dict, session: Session = Depends(get_session)):
    """
    Atualiza os dados de um cliente existente.

    Parâmetros:
    - id (int): ID do cliente a ser atualizado.
    - body (dict): Dados que devem ser atualizados.
    - session (Session): Sessão do banco de dados (injeção de dependência).

    Retorna:
    - JSONResponse com status, mensagem e dados do cliente atualizado.
    - HTTP 404 se o cliente não for encontrado.
    - HTTP 409 se houver conflito de CPF ou email.
    """
    db_client = session.scalar(
        select(Client).where(
            (Client.id == id) & (Client.deleted == False)
        )
    )

    if not db_client:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado!"
        )

    for chave, valor in body.items():
        if chave == "cpf":
            cpf = valor.replace("-", "").replace(".", "")
            db_client_validacao = session.scalar(
                select(Client).where(
                    (Client.cpf == cpf) & (Client.deleted == False) & (Client.id != id)
                )
            )
            if db_client_validacao:
                raise HTTPException(
                    status_code=409,
                    detail="Cliente com esse CPF já cadastrado!"
                )
            valor = cpf

        if chave == "email":
            db_client_validacao = session.scalar(
                select(Client).where(
                    (Client.email == valor) & (Client.deleted == False) & (Client.id != id)
                )
            )
            if db_client_validacao:
                raise HTTPException(
                    status_code=409,
                    detail="Cliente com esse email já cadastrado!"
                )

        if not hasattr(db_client, chave):
            continue
        setattr(db_client, chave, valor)

    session.commit()
    session.refresh(db_client)

    response = {
        "status": "success",
        "message": "Cliente alterado com sucesso.",
        "cliente": {
            "id": db_client.id,
            "email": db_client.email,
            "cpf": db_client.cpf,
            "nome": db_client.nome
        }
    }

    return JSONResponse(content=response, status_code=200)


@router.delete("/{id}")
def deletar_cliente(id: int, session: Session = Depends(get_session)):
    """
    Deleta (soft delete) um cliente existente.

    Parâmetros:
    - id (int): ID do cliente a ser deletado.
    - session (Session): Sessão do banco de dados (injeção de dependência).

    Retorna:
    - JSONResponse com status, mensagem e dados do cliente deletado.
    - HTTP 404 se o cliente não for encontrado.
    """
    db_client = session.scalar(
        select(Client).where(
            (Client.id == id) & (Client.deleted == False)
        )
    )

    if not db_client:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado!"
        )

    db_client.deleted = True
    session.commit()
    session.refresh(db_client)

    response = {
        "status": "success",
        "message": "Cliente deletado com sucesso.",
        "cliente": {
            "id": db_client.id,
            "email": db_client.email,
            "cpf": db_client.cpf,
            "nome": db_client.nome
        }
    }

    return JSONResponse(content=response, status_code=200)