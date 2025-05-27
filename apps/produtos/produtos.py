from fastapi import Depends, FastAPI, HTTPException, APIRouter, Query
from fastapi.responses import JSONResponse 
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional

from database import get_session
from models import Produto
from helpers.validacao import verificar_campos_obrigatorios
from helpers.security import verificar_token

router = APIRouter()


@router.get("/")
def listar_produtos(
    categoria: Optional[str] = Query(None),
    preco: Optional[str] = Query(None),
    disponibilidade: Optional[bool] = Query(None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    usuario: str = Depends(verificar_token)
    ):
    """
    Lista produtos com filtros opcionais.

    Parâmetros:
    - categoria (str, opcional): Categoria do produto.
    - preco (str, opcional): Preço exato.
    - disponibilidade (bool, opcional): Disponibilidade do produto.
    - limit (int): Quantidade máxima de resultados.
    - offset (int): Deslocamento inicial.
    - session (Session): Sessão do banco de dados.
    - usuario (str): Nome de usuário injetado automaticamente via Depends(verificar_token).
        Garante que apenas usuários autenticados possam acessar este endpoint.

    Retorna:
    - JSONResponse com lista de produtos e metadados.
    - HTTP 404 se nenhum produto for encontrado.
    """
    
    query = select(Produto).where(Produto.deleted == False)

    if categoria:
        query = query.where(Produto.categoria.ilike(f"%{categoria}%"))

    if preco:
        query = query.where(Produto.preco == preco)

    if disponibilidade is not None:
        query = query.where(Produto.disponibilidade == disponibilidade)

    query = query.limit(limit).offset(offset)

    db_produtos = session.scalars(query).all()

    if not db_produtos:
        raise HTTPException(
            status_code=404,
            detail="Produtos não encontrados com os parâmetros solicitados!"
        )

    produtos = [
        {
            "id": produto.id,
            "descricao": produto.descricao,
            "codigo_barras": produto.codigo_barras,
            "estoque": produto.estoque,
            "data_validade": str(produto.data_validade),
            "imagens": produto.imagens,
            "preco": produto.preco,
            "categoria": produto.categoria,
            "disponibilidade": produto.disponibilidade
        }
        for produto in db_produtos
    ]

    response = {
        "status": "success",
        "message": "Produtos encontrados com sucesso.",
        "usuario": usuario,
        "total": len(produtos),
        "produtos": produtos
    }

    return JSONResponse(content=response, status_code=200)


@router.get("/{id}")
def buscar_produto_por_id(id: int, session: Session = Depends(get_session), usuario: str = Depends(verificar_token)):
    """
    Busca um produto pelo ID.

    Parâmetros:
    - id (int): ID do produto.
    - session (Session): Sessão do banco de dados.
    - usuario (str): Nome de usuário injetado automaticamente via Depends(verificar_token).
        Garante que apenas usuários autenticados possam acessar este endpoint.

    Retorna:
    - JSONResponse com os dados do produto.
    - HTTP 404 se o produto não for encontrado.
    """
    
    db_produto = session.scalar(
        select(Produto).where(
            (Produto.id == id) & (Produto.deleted == False)
        )
    )

    if not db_produto:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado!"
        )

    response = {
        "status": "success",
        "message": "Produto encontrado com sucesso.",
        "usuario": usuario,
        "produto": {
            "id": db_produto.id,
            "descricao": db_produto.descricao,
            "codigo_barras": db_produto.codigo_barras,
            "estoque": db_produto.estoque,
            "data_validade": str(db_produto.data_validade),
            "imagens": db_produto.imagens,
            "preco": db_produto.preco,
            "categoria": db_produto.categoria,
            "disponibilidade": db_produto.disponibilidade
        }
    }

    return JSONResponse(content=response, status_code=200)


@router.post("/")
def criar_produto(body: dict, session: Session = Depends(get_session), usuario: str = Depends(verificar_token)):
    """
    Cria um novo produto.

    Parâmetros:
    - body (dict): Dados do produto.
    - session (Session): Sessão do banco de dados.
    - usuario (str): Nome de usuário injetado automaticamente via Depends(verificar_token).
        Garante que apenas usuários autenticados possam acessar este endpoint.

    Retorna:
    - JSONResponse com dados do produto criado.
    - HTTP 400 se faltar campos obrigatórios.
    - HTTP 409 se produto já existir.
    """
    obrigatorios = ["descricao", "codigo_barras", "estoque", "data_validade", "preco", "categoria"]
    validacao = verificar_campos_obrigatorios(obrigatorios=obrigatorios, body=body)
    if not validacao:
        raise HTTPException(
            status_code=400,
            detail="Informação obrigatória para cadastro não informada."
        )

    db_produto = session.scalar(
        select(Produto).where(
            (Produto.codigo_barras == body["codigo_barras"]) & (Produto.deleted == False)
        )
    )
    if db_produto:
        raise HTTPException(
            status_code=409,
            detail="Produto com essas informações já cadastrado!"
        )

    db_produto = Produto(
        descricao=body["descricao"],
        codigo_barras=body["codigo_barras"],
        estoque=body["estoque"],
        data_validade=body["data_validade"],
        imagens=body.get("imagens", []),
        preco=body["preco"],
        categoria=body["categoria"]
    )

    session.add(db_produto)
    session.commit()
    session.refresh(db_produto)

    response = {
        "status": "success",
        "message": "Produto cadastrado com sucesso.",
        "usuario": usuario,
        "produto": {
            "id": db_produto.id,
            "descricao": db_produto.descricao,
            "codigo_barras": db_produto.codigo_barras,
            "estoque": db_produto.estoque,
            "data_validade": str(db_produto.data_validade),
            "imagens": db_produto.imagens,
            "preco": db_produto.preco,
            "categoria": db_produto.categoria,
            "disponibilidade": db_produto.disponibilidade
        }
    }

    return JSONResponse(content=response, status_code=201)


@router.put("/{id}")
def atualizar_produto(id: int, body: dict, session: Session = Depends(get_session), usuario: str = Depends(verificar_token)):
    """
    Atualiza um produto existente.

    Parâmetros:
    - id (int): ID do produto.
    - body (dict): Dados para atualização.
    - session (Session): Sessão do banco de dados.
    - usuario (str): Nome de usuário injetado automaticamente via Depends(verificar_token).
        Garante que apenas usuários autenticados possam acessar este endpoint.

    Retorna:
    - JSONResponse com dados do produto atualizado.
    - HTTP 404 se produto não for encontrado.
    - HTTP 409 se houver conflito de dados únicos.
    """
    db_produto = session.scalar(
        select(Produto).where(
            (Produto.id == id) & (Produto.deleted == False)
        )
    )

    if not db_produto:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado!"
        )

    if "codigo_barras" in body:
        db_produto_validacao = session.scalar(
            select(Produto).where(
                (Produto.codigo_barras == body["codigo_barras"]) & (Produto.deleted == False) & (Produto.id != id)
            )
        )
        if db_produto_validacao:
            raise HTTPException(
                status_code=409,
                detail="Já existe algum produto cadastrado com esta informação única!"
            )

    for chave, valor in body.items():
        if not hasattr(db_produto, chave):
            continue
        setattr(db_produto, chave, valor)

    session.commit()
    session.refresh(db_produto)

    response = {
        "status": "success",
        "message": "Produto alterado com sucesso.",
        "usuario": usuario,
        "produto": {
            "id": db_produto.id,
            "descricao": db_produto.descricao,
            "codigo_barras": db_produto.codigo_barras,
            "estoque": db_produto.estoque,
            "data_validade": str(db_produto.data_validade),
            "imagens": db_produto.imagens,
            "preco": db_produto.preco,
            "categoria": db_produto.categoria,
            "disponibilidade": db_produto.disponibilidade
        }
    }

    return JSONResponse(content=response, status_code=200)


@router.delete("/{id}")
def deletar_produto(id: int, session: Session = Depends(get_session), usuario: str = Depends(verificar_token)):
    """
    Deleta (soft delete) um produto pelo ID.

    Parâmetros:
    - id (int): ID do produto.
    - session (Session): Sessão do banco de dados.
    - usuario (str): Nome de usuário injetado automaticamente via Depends(verificar_token).
        Garante que apenas usuários autenticados possam acessar este endpoint.

    Retorna:
    - JSONResponse com dados do produto deletado.
    - HTTP 404 se produto não for encontrado.
    """
    db_produto = session.scalar(
        select(Produto).where(
            (Produto.id == id) & (Produto.deleted == False)
        )
    )

    if not db_produto:
        raise HTTPException(
            status_code=404,
            detail="Produto não encontrado!"
        )

    db_produto.deleted = True
    session.commit()
    session.refresh(db_produto)

    response = {
        "status": "success",
        "message": "Produto deletado com sucesso.",
        "usuario": usuario,
        "produto": {
            "id": db_produto.id,
            "descricao": db_produto.descricao,
            "codigo_barras": db_produto.codigo_barras,
            "estoque": db_produto.estoque,
            "data_validade": str(db_produto.data_validade),
            "imagens": db_produto.imagens,
            "preco": db_produto.preco,
            "categoria": db_produto.categoria,
            "disponibilidade": db_produto.disponibilidade
        }
    }

    return JSONResponse(content=response, status_code=200)