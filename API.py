from fastapi import fastapi # ferramenta principal
from pydantic import BaseModel # Biblioteca que o FastAPI usa para validar dados
import random # Biblioteca para gerar coisas aleatórias
import string # Biblioteca de constantes uteis, como listas prontas de letras e numeros

app = FastAPI() # criando instancia da aplicação

class LinkRequest(BaseModel): # "Molde" esperado de como os dados chegam
    url_completa: str # "toda requisição precisa ter um campo chamado url_completa do tipo str"

@app.post('/encurtar') # Quando chegar uma requisição do tipo POST no endereço /encurtar, execute a função abaixo
def encurtar_link(request: LinkRequest): # Ja recebe os dados validados e prontos para uso (parametro request, tipo LinkRequest)
    pass

def gerar_codigo_curto(tamanho: int=6) -> str:
    caracteres = string.ascii_letters + string.digits # pool de caracteres possiveis (letras + numeros)
    return ''.join(random.choices(caracteres, k=tamanho)) # devolve uma lista de caracteres soltos, unificados depois em uma string pelo join
