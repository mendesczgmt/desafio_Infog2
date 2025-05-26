from fastapi import FastAPI 
from apps.infog2 import auth
from apps.clients import main

app = FastAPI()  

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(main.router, prefix="/clients", tags=["clients"])