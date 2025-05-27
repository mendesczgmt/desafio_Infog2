from fastapi import Depends, FastAPI, HTTPException, APIRouter, Query
from fastapi.responses import JSONResponse 
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from datetime import datetime


from database import get_session
from models import Pedido, ItensPedido, Client, Produto
from helpers.validacao import verificar_campos_obrigatorios
from helpers.security import verificar_token


router = APIRouter()


@router.get("/")
def listar_pedidos(
    periodo_inicio: Optional[datetime] = Query(None),
    periodo_fim: Optional[datetime] = Query(None),
    secao: Optional[str] = Query(None),
    id_pedido: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    cliente: Optional[int] = Query(None),
    session: Session = Depends(get_session),
    usuario: str = Depends(verificar_token)
):
    """
    Lista pedidos com filtros opcionais.

    Parâmetros:
    - periodo_inicio (datetime, opcional): Data e hora inicial para filtrar os pedidos.
    - periodo_fim (datetime, opcional): Data e hora final para filtrar os pedidos.
    - secao (str, opcional): Filtro pela categoria dos produtos presentes nos pedidos.
    - id_pedido (int, opcional): Filtro pelo ID do pedido.
    - status (str, opcional): Filtro pelo status do pedido.
    - cliente (int, opcional): Filtro pelo ID do cliente.
    - session (Session): Sessão do banco de dados.
    - usuario (str): Usuário autenticado via token JWT.

    Retorna:
    - JSONResponse contendo a mensagem, total de pedidos e lista dos pedidos filtrados.
    - HTTP 404 se nenhum pedido for encontrado.
    """
    query = select(Pedido).where(Pedido.deleted == False)

    if periodo_inicio:
        query = query.where(Pedido.created_at >= periodo_inicio)
    if periodo_fim:
        query = query.where(Pedido.created_at <= periodo_fim)
    if id_pedido:
        query = query.where(Pedido.id == id_pedido)
    if status:
        query = query.where(Pedido.status == status)
    if cliente:
        query = query.where(Pedido.cliente_id == cliente)
    if secao:
        query = query.join(Pedido.itens).where(Produto.categoria == secao)

    pedidos = session.scalars(query).all()

    if len(pedidos) == 0:
        raise HTTPException(
            status_code=404,
            detail="Pedidos não encontrados com os parâmetros solicitados!"
        )

    pedidos = [
        {
            "id": pedido.id,
            "cliente id": pedido.cliente_id,
            "status": pedido.status,
            "preço total": pedido.preco_total,
        }
        for pedido in pedidos
    ]

    data = {
        "mensagem": "Pedidos encontrados com sucesso",
        "usuario": usuario,
        "total": len(pedidos),
        "pedidos": pedidos
    }

    return JSONResponse(content=data, status_code=200)


@router.get("/{id}")
def teste_de_get(
    id: int, 
    session: Session = Depends(get_session),
    usuario: str = Depends(verificar_token)
):
    """
    Obtém informações detalhadas de um pedido específico.

    Parâmetros:
    - id (int): ID do pedido a ser recuperado.
    - session (Session): Sessão do banco de dados.
    - usuario (str): Usuário autenticado via token JWT.

    Retorna:
    - JSONResponse contendo a mensagem e os detalhes do pedido.
    - HTTP 404 se o pedido não for encontrado.
    """
    db_pedido = session.scalar(
        select(Pedido).where(
            (Pedido.id == id) & (Pedido.deleted == False)
        )
    )

    if not db_pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado!"
        )

    data = {
        "mensagem": "Pedido encontrado com sucesso",
        "usuario": usuario,
        "pedido": {
            "cliente id": db_pedido.cliente_id,
            "status": db_pedido.status,
            "preço total": db_pedido.preco_total,
        }
    }

    return JSONResponse(content=data, status_code=200)


@router.post("/")
def criar_pedido(
    body: dict, 
    session: Session = Depends(get_session),
    usuario: str = Depends(verificar_token)
):
    """
    Cria um novo pedido contendo múltiplos produtos.

    Valida a existência do cliente, a disponibilidade de estoque e o status de cada produto antes de criar o pedido.

    Parâmetros:
    - body (dict): Dados do pedido, contendo o `cliente_id` e a lista de `produtos` com `produto_id` e `quantidade`.
    - session (Session): Sessão do banco de dados.
    - usuario (str): Usuário autenticado via token JWT.

    Retorna:
    - JSONResponse com mensagem de sucesso, ID do pedido criado, total do pedido e lista de produtos.
    - HTTP 400 ou 404 em caso de erros de validação.
    """
    obrigatorios = ["cliente_id", "produtos"]

    if not verificar_campos_obrigatorios(obrigatorios=obrigatorios, body=body):
        raise HTTPException(
            status_code=400,
            detail="Informação obrigatória para cadastro não informada",
        )

    db_client = session.scalar(
        select(Client).where(
            (Client.id == body["cliente_id"]) & (Client.deleted == False)
        )
    )

    if not db_client:
        raise HTTPException(
            status_code=404,
            detail="Cliente não encontrado!"
        )

    if len(body["produtos"]) == 0:
        raise HTTPException(
            status_code=404,
            detail="Não é possível criar pedido sem os produtos",
        )

    total = 0
    ids_itens = []
    produtos_list = []

    for produto in body["produtos"]:
        obrigatorios = ["produto_id", "quantidade"]

        if not verificar_campos_obrigatorios(obrigatorios=obrigatorios, body=produto):
            raise HTTPException(
                status_code=404,
                detail="Informação obrigatória para cadastro de produto não informada",
            )

        db_produto = session.scalar(
            select(Produto).where(
                (Produto.id == produto["produto_id"]) & (Produto.deleted == False)
            )
        )

        if not db_produto:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado!"
            )
        elif not db_produto.disponibilidade:
            raise HTTPException(
                status_code=404,
                detail="Produto indisponível!"
            )
        elif db_produto.estoque < produto["quantidade"]:
            raise HTTPException(
                status_code=404,
                detail="Quantidade não disponível!"
            )

        db_produto.estoque -= produto["quantidade"]
        total += db_produto.preco

        db_item_produto = ItensPedido(
            pedido_id=None,
            produto_id=produto['produto_id'],
            quantidade=produto['quantidade'],
            preco=db_produto.preco,
        )
        session.add(db_item_produto)
        session.commit()
        session.refresh(db_item_produto)

        ids_itens.append(db_item_produto.id)
        produtos_list.append(
            {'produto_id': produto['produto_id'], 'quantidade': produto['quantidade']}
        )

    db_pedido = Pedido(cliente_id=body["cliente_id"], status="PENDENTE", preco_total=total)
    session.add(db_pedido)
    session.commit()
    session.refresh(db_pedido)

    for id in ids_itens:
        db_item = session.scalar(
            select(ItensPedido).where(
                (ItensPedido.id == id) & (Produto.deleted == False)
            )
        )
        db_item.pedido_id = db_pedido.id
        session.commit()
        session.refresh(db_item_produto)

    data = {
        "mensagem": "Pedido cadastrado com sucesso",
        "usuario": usuario,
        "pedido_id": db_pedido.id,
        "total do pedido": db_pedido.preco_total,
        "produtos": produtos_list
    }

    return JSONResponse(content=data, status_code=200)


@router.put("/{id}")
def atualizar_pedido(
    id: int, 
    body: dict, 
    session: Session = Depends(get_session),
    usuario: str = Depends(verificar_token)
):
    """
    Atualiza informações de um pedido específico.

    Permite modificar qualquer campo existente no modelo `Pedido` com base nos dados enviados no `body`.

    Parâmetros:
    - id (int): ID do pedido a ser atualizado.
    - body (dict): Dados a serem atualizados no pedido.
    - session (Session): Sessão do banco de dados.
    - usuario (str): Usuário autenticado via token JWT.

    Retorna:
    - JSONResponse com mensagem de sucesso e detalhes do pedido atualizado.
    - HTTP 404 se o pedido não for encontrado.
    """
    db_pedido = session.scalar(
        select(Pedido).where(
            (Pedido.id == id) & (Pedido.deleted == False)
        )
    )

    if not db_pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado!"
        )

    for chave in body.keys():
        if not hasattr(db_pedido, chave):
            continue
        setattr(db_pedido, chave, body[chave])

    session.commit()
    session.refresh(db_pedido)

    data = {
        "mensagem": "Pedido alterado com sucesso",
        "usuario": usuario,
        "pedido": {
            "cliente id": db_pedido.cliente_id,
            "status": db_pedido.status,
            "preço total": db_pedido.preco_total,
        }
    }

    return JSONResponse(content=data, status_code=200)


@router.delete("/{id}")
def deletar_pedido(
    id: int, 
    session: Session = Depends(get_session),
    usuario: str = Depends(verificar_token)
):
    """
    Exclui (soft delete) um pedido específico.

    Marca o pedido como deletado, mantendo o registro no banco de dados, mas excluindo-o das operações comuns.

    Parâmetros:
    - id (int): ID do pedido a ser excluído.
    - session (Session): Sessão do banco de dados.
    - usuario (str): Usuário autenticado via token JWT.

    Retorna:
    - JSONResponse com mensagem de sucesso e detalhes do pedido excluído.
    - HTTP 404 se o pedido não for encontrado.
    """
    db_pedido = session.scalar(
        select(Pedido).where(
            (Pedido.id == id) & (Pedido.deleted == False)
        )
    )

    if not db_pedido:
        raise HTTPException(
            status_code=404,
            detail="Pedido não encontrado!"
        )

    db_pedido.deleted = True
    session.commit()
    session.refresh(db_pedido)

    data = {
        "mensagem": "Pedido deletado com sucesso",
        "usuario": usuario,
        "pedido": {
            "cliente id": db_pedido.cliente_id,
            "status": db_pedido.status,
            "preço total": db_pedido.preco_total,
        }
    }

    return JSONResponse(content=data, status_code=200)
