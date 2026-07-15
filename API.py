from fastapi import fastapi # ferramenta principal
from pydantic import BaseModel # Biblioteca que o FastAPI usa para validar dados
import random # Biblioteca para gerar coisas aleatórias
import string # Biblioteca de constantes uteis, como listas prontas de letras e numeros
from sqlalchemy import create_engine
from sqlalchemy import sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base


app = FastAPI() # criando instancia da aplicação

class LinkRequest(BaseModel): # "Molde" esperado de como os dados chegam
    url_completa: str # "toda requisição precisa ter um campo chamado url_completa do tipo str"

@app.post('/encurtar') # Quando chegar uma requisição do tipo POST no endereço /encurtar, execute a função abaixo
def encurtar_link(request: LinkRequest): # Ja recebe os dados validados e prontos para uso (parametro request, tipo LinkRequest)
    pass

def gerar_codigo_curto(tamanho: int=6) -> str:
    caracteres = string.ascii_letters + string.digits # pool de caracteres possiveis (letras + numeros)
    return ''.join(random.choices(caracteres, k=tamanho)) # devolve uma lista de caracteres soltos, unificados depois em uma string pelo join

DATABASE_URL = "postgresql://usuario:senha@db:5432/encurtador" # endereço do banco de dados

engine = create_engine(DATABASE_URL) # cria o Motor de conexão com o banco
SessionLocal = sessionmaker(bind=engine) # cria um criador de sessões

Base = declarative_base() # cria uma classe base da qual todas as tabelas vão herdar

class Link(Base): # define a tabela links
    __tablename__ = 'links' # nome da tabela no banco de dados
    id = Column(Integer, primary_key=True) # Coluna id da tabela (tipo inteiro e chave primaria)
    url_completa = Column(String, nullable=False) # Coluna da url completa (Banco impede o valor vazio)
    codigo_curto = Column(String, nullable=False, unique=True) # Coluna do link encurtado(O proprio banco impede valores repetidos)
    