from datetime import datetime, date

from sqlalchemy import func, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, registry


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
    valor_venda: Mapped[float] = mapped_column()
    codigo_barras: Mapped[str] = mapped_column(unique=True)
    secao: Mapped[str] = mapped_column()
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

    