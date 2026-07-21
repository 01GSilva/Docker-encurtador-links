FROM python:3.11-slim

WORKDIR /API

# Instala dependencias (aproveita o cache do Docker)
COPY api-requirements.txt /API/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copia o codigo como root
COPY API.py /API

# Cria o usuario de servico sem diretorio home proprio
RUN groupadd -r apiuser \
    && useradd -r -g apiuser -M apiuser \
    && chown -R apiuser:apiuser /API

# Troca para o usuario
USER apiuser

EXPOSE 8000

CMD ["uvicorn", "API:app", "--host", "0.0.0.0", "--port", "8000"]