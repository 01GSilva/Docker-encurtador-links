FROM python:3.11-slim

WORKDIR /worker

COPY worker-requirements.txt /worker/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py /worker

RUN groupadd -r workeruser \
    && useradd -r -g workeruser -M workeruser \
    && chown -R workeruser:workeruser /worker

USER workeruser

CMD ["python", "worker.py"]