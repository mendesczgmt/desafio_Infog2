from datetime import datetime, date

from sqlalchemy import func, Boolean, JSON, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship


table_registry = registry()


@table_registry.mapped_as_dataclass
class User:
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    senha: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default='false'
    )
    admin: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default='false'
    )

@table_registry.mapped_as_dataclass
class Client:
    __tablename__ = 'clients'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    cpf: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default='false'
    )
    nome: Mapped[str] = mapped_column(unique=False, default=None)


@table_registry.mapped_as_dataclass
class Produto:
    __tablename__ = 'produtos'
    
    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    descricao: Mapped[str] = mapped_column()
    codigo_barras: Mapped[str] = mapped_column(unique=True)
    estoque: Mapped[int] = mapped_column()
    data_validade: Mapped[date] = mapped_column(nullable=True)
    imagens: Mapped[list] = mapped_column(JSON, nullable=True)
    preco: Mapped[float] = mapped_column()
    categoria: Mapped[str] = mapped_column()    

    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )
    deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default='false'
    )
    disponibilidade: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default='true'
    )


@table_registry.mapped_as_dataclass
class ItensPedido:
    __tablename__ = "itens_pedidos"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), nullable=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    
    quantidade: Mapped[int] = mapped_column()
    preco: Mapped[float] = mapped_column()

    pedido: Mapped["Pedido"] = relationship(
        "Pedido",
        back_populates="itens",
        init=False
    )

@table_registry.mapped_as_dataclass
class Pedido:
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clients.id"))
    status: Mapped[str] = mapped_column(String)

    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now(), onupdate=func.now()
    )

    itens: Mapped[list["ItensPedido"]] = relationship(
        "ItensPedido",
        back_populates="pedido",
        init=False
    )
    preco_total: Mapped[float] = mapped_column()
    deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default='false'
    )