import json
import random
import string
from datetime import datetime
import redis
from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# ========== Configuração do Banco de Dados (Postgres) =====

DATABASE_URL = "postgresql://usuario:senha@db:5432/encurtador" # endereço do banco de dados

engine = create_engine(DATABASE_URL) # cria o Motor de conexão com o banco
SessionLocal = sessionmaker(bind=engine) # cria um criador de sessões

Base = declarative_base() # cria uma classe base da qual todas as tabelas vão herdar

def get_db(): # Função para abrir e fechar a sessão para liberar a conexão
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# == Configuração da Fila (Redis) ==========

redis_client = redis.Redis(host='fila', port=6379, decode_responses=True) # 'fila' como nome de serviço, porta padrão do Redis e decodificação devolvendo str

def enviar_para_fila(codigo_curto: str):
    dados_clique = {
        'codigo_curto': codigo_curto,
        'timestamp': datetime.utcnow().isoformat() # transforma o momento UTC atual em um texto padronizado
    }
    redis_client.rpush('fila_cliques', json.dumps(dados_clique)) # Insere um item no final da fila (rpush). Converte um dicionario Python em Json (json.dumbs)

# == Modelo (Tabela) ==========

class Link(Base):
    __tablename__ = 'links' # nome da tabela no banco de dados

    id = Column(Integer, primary_key=True) # Coluna id da tabela (tipo inteiro e chave primaria)
    url_completa = Column(String, nullable=False) # Coluna da url completa (Banco impede o valor vazio)
    codigo_curto = Column(String, nullable=False, unique=True) # Coluna do link encurtado(O proprio banco impede valores repetidos)

Base.metadata.create_all(engine) # cria a tabela Links somente se ela ainda não constar no banco. Caso exista, não faz nada

# == Schema de entrada (validade) ==========

class LinkRequest(BaseModel):
    url_completa: str # "toda requisição precisa ter um campo chamado url_completa do tipo str"


# == Função auxiliar para gerar código ==========

def gerar_codigo_curto(tamanho: int=6) -> str:
    caracteres = string.ascii_letters + string.digits # pool de caracteres possiveis (letras + numeros)
    return ''.join(random.choices(caracteres, k=tamanho)) # devolve uma lista de caracteres soltos, unificados depois em uma string pelo join

# == Aplicação ==========

app = FastAPI()

# ===== Rota 1 ==========

@app.post('/encurtar') # Quando chegar uma requisição do tipo POST no endereço /encurtar, execute a função abaixo
def encurtar_link(request: LinkRequest, db: Session = Depends(get_db)): # Ja recebe os dados validados e prontos para uso (parametro request, tipo LinkRequest)
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

# ===== Rota 2 ==========

@app.get('/{codigo_curto}') # Metodo Get, pois está buscando algo que ja existe
def redirecionar(codigo_curto:str, db:Session = Depends(get_db)):
    link = db.querry(Link).filter_by(codigo_curto=codigo_curto).first() # Busca filtrando pela coluna "codigo_curto"
    
    if not link: # Caso alguém acesse um código que não exista
        return{'erro': 'Link não encontrado'}

    resposta = RedirectResponse(url=link.url_completa) # Ferramenta do FastAPI que gera uma resposta de HTTP direta de redirecionamento

    enviar_para_fila(codigo_curto) # "Fire and forget" que a API faz para a fila

    return resposta # Devolve o redirecionamento