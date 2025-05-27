Desafio Infog2

Pré-requisitos
Python 3.11 (ou compatível com seu projeto)

Poetry instalado (instruções de instalação)

Como rodar o projeto
Clone o repositório

bash
Copiar
Editar
git clone https://github.com/mendesczgmt/desafio_Infog2.git
cd desafio_Infog2
Instale as dependências com Poetry

bash
Copiar
Editar
poetry install
Ative o ambiente virtual do Poetry

bash
Copiar
Editar
poetry shell
Configure variáveis de ambiente

Crie um arquivo .env na raiz do projeto (se ainda não existir) com as variáveis necessárias, por exemplo:

ini
Copiar
Editar
SECRET_KEY="@1NF0G2#"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL="postgresql+asyncpg://user:password@localhost/dbname"
Ajuste as variáveis conforme seu ambiente.

Execute a aplicação

bash
Copiar
Editar
poetry run fastapi dev infog2/main.py
Ou, se estiver dentro do shell do Poetry:

bash
Copiar
Editar
fastapi dev infog2/main.py