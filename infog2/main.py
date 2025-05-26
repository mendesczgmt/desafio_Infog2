from fastapi import FastAPI 
from apps.infog2 import auth
from apps.clients import clients
from apps.produtos import produtos
from apps.pedidos import pedidos

app = FastAPI()  

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(clients.router, prefix="/clients", tags=["clients"])
app.include_router(produtos.router, prefix="/produtos", tags=["produtos"])
app.include_router(pedidos.router, prefix="/pedidos", tags=["pedidos"])