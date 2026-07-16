from fastapi import fastapi # ferramenta principal
from pydantic import BaseModel # Biblioteca que o FastAPI usa para validar dados
import random # Biblioteca para gerar coisas aleatórias
import string # Biblioteca de constantes uteis, como listas prontas de letras e numeros
from sqlalchemy import create_engine
from sqlalchemy import sessionmaker
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base


app = FastAPI() # criando instancia da aplicação

# ===== "Molde" esperado de como os dados chegam =======================================================================
class LinkRequest(BaseModel):
    url_completa: str # "toda requisição precisa ter um campo chamado url_completa do tipo str"


# ======================================================================================================================
def gerar_codigo_curto(tamanho: int=6) -> str:
    caracteres = string.ascii_letters + string.digits # pool de caracteres possiveis (letras + numeros)
    return ''.join(random.choices(caracteres, k=tamanho)) # devolve uma lista de caracteres soltos, unificados depois em uma string pelo join


# ===== Configuração do Banco de Dados =================================================================================
DATABASE_URL = "postgresql://usuario:senha@db:5432/encurtador" # endereço do banco de dados

engine = create_engine(DATABASE_URL) # cria o Motor de conexão com o banco
SessionLocal = sessionmaker(bind=engine) # cria um criador de sessões

Base = declarative_base() # cria uma classe base da qual todas as tabelas vão herdar


# ===== Função para abrir e fechar a sessão para liberar a conexão =====================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===== Define a Tabela "Links" no Banco de dados ======================================================================
class Link(Base):
    __tablename__ = 'links' # nome da tabela no banco de dados
    id = Column(Integer, primary_key=True) # Coluna id da tabela (tipo inteiro e chave primaria)
    url_completa = Column(String, nullable=False) # Coluna da url completa (Banco impede o valor vazio)
    codigo_curto = Column(String, nullable=False, unique=True) # Coluna do link encurtado(O proprio banco impede valores repetidos)



# ===== Rota 1  =========================================================================================================
@app.post('/encurtar') # Quando chegar uma requisição do tipo POST no endereço /encurtar, execute a função abaixo
def encurtar_link(request: LinkRequest, db: Session = Depends(get_db())): # Ja recebe os dados validados e prontos para uso (parametro request, tipo LinkRequest)
    link_existente = db.querry(Link).filter_by(url_completa=request.url_completa).first()
    # Verifica se ja existe a URL completa no banco de dados
    if link_existente:
        return {'link_curto': link_existente.codigo_curto}
    
    while True: # checa em loop se ja existe no banco um código igual ao codigo gerado
        novo_codigo = gerar_codigo_curto()
        colisao = db.querry(Link).filter_by(codigo_curto=novo_codigo).first()
        if not colisao:
            break # caso não haja colisão, ele encerra o loop
    
    novo_link = Link(url_completa=request.url_completa, codigo_curto=novo_codigo)
    # Instancia - cria uma nova linha na tabela link para salvar o código gerado
    db.add(novo_link) # comunica a sessão para inserir um novo objeto no banco
    db.commit() # grava efetivamente no banco
    return {'link_curto': novo_codigo}