import json
import redis
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

# === Configuração do Banco de dados (Postgres) ===

DATABASE_URL = 'postgresql://usuario:senha@db:5432/encurtador'

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# === Tabela de registro ===

class Clique(Base):
    __tablename__ = 'cliques'
    id = Column(Integer, primary_key=True)
    codigo_curto = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)

Base.metadata.create_all(engine)

# === Configuração da fila ===

redis_client = redis.Redis(host='fila', port=6379, decode_responses=True)

# === Loop principal ===

def processar_cliques():
    while True:
        try:
            _, dado_bruto = redis_client.blpop('fila_cliques') # espera pausado até algum item aparecer na fila
            # retorna tupla com valores 'nome da lista de origem' e 'item'. O nome da lista de origem é ignorado pela convenção '_' (fila_cliques).
            dados_clique = json.loads(dado_bruto) # reconstrói o dicionario python original

            db = SessionLocal()
            try:
                novo_registro = Clique(
                    codigo_curto = dados_clique['codigo_curto'],
                    timestamp = dados_clique['timestamp']
                )
                db.add(novo_registro)
                db.commit()
                print(f"Clique registrado: {dados_clique['codigo_curto']}")
            finally:
                db.close()

        except Exception as erro:
            print(f'Erro ao processar clique, tentando novamente: {erro}')

if __name__ == '__main__':
    processar_cliques()