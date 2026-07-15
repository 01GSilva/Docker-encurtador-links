FROM python:3.11-slim

WORKDIR /API

# Instala dependencias (aproveita o cache do Docker)
COPY requirements.txt /API
RUN pip install --no-cache-dir -r requirements.txt

# Copia o codigo como root
COPY API.py /API

# Cria o usuario de servico sem diretorio home proprio
RUN groupadd -r apiuser \
    && useradd -r -g apiuser -M apiuser \
    && chown -R apiuser:apiuser /API

# Troca para o usuario
USER apiuser

CMD ["python", "API.py"]