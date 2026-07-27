# Encurtador de URLs com Analytics Assíncrono

Projeto idealizado como prática para consolidar os conhecimentos do curso [Containers e Docker: empacotamento, isolamento e gestão](https://cursos.alura.com.br/course/containers-na-pratica-com-docker), recentemente concluído. O foco do projeto é a aplicação prática de conceitos de containers e Docker: isolamento de serviços, persistência de dados, comunicação em rede interna e processamento assíncrono com fila de mensagens, mais do que a complexidade da aplicação em si.

## O problema

Um encurtador de URLs clássico, mas desenhado para exigir múltiplos serviços colaborando: criar um link curto precisa de resposta imediata ao usuário, enquanto registrar analytics de cliques (quem acessou, quando) pode, e deve, ser processado em segundo plano, sem atrasar quem está sendo redirecionado.

## Arquitetura

O projeto possui 4 serviços isolados em containers próprios que se comunicam entre si: **API**, **worker**, **fila** e **banco de dados**.

O sistema opera em dois fluxos principais:

- **Fluxo 1 — Criar link curto (síncrono):** a API recebe a requisição de encurtamento, checa no banco se já existe um link curto para aquela URL e devolve, ou gera um novo código, salva no banco e devolve, tudo dentro da mesma requisição, sem fila envolvida.

- **Fluxo 2 — Redirecionar (síncrono + assíncrono):** a API recebe o acesso ao link curto, busca o endereço completo no banco e **redireciona o usuário imediatamente**. Só depois disso, ela dispara as informações do clique para a fila (Redis), de forma *fire and forget*, sem esperar confirmação. O **worker**, rodando em segundo plano, consome essa fila e grava o registro do clique no banco, de forma totalmente desacoplada da experiência do usuário.

```
Usuário → API ──┬─→ Postgres (links e cliques)
                 └─→ Redis (fila de cliques) → Worker → Postgres
```

## Decisões técnicas e trade-offs'

**Postgres em vez de SQLite ou Redis como banco principal**
SQLite guarda tudo em um único arquivo dentro do container, o que eliminaria a necessidade real de volumes, um dos temas centrais do projeto. Redis já era usado como fila; reaproveitá-lo como banco principal misturaria responsabilidades que fazem mais sentido separadas. Postgres é o banco relacional mais usado no mercado, o que também agrega valor de aprendizado.

**Fila assíncrona só para o registro de clique, não para a criação do link**
Criar um link exige resposta imediata (o usuário está esperando ver o resultado). Registrar um clique não precisa disso, o usuário só quer ser redirecionado o mais rápido possível. Colocar essa etapa em uma fila evita que o redirecionamento fique refém da velocidade do banco de dados ou de um pico de tráfego.

**Redis como fila (em vez de RabbitMQ)**
Para um primeiro projeto com múltiplos containers, Redis oferece uma curva de aprendizado mais simples, mantendo ainda assim relevância real de mercado.

**Geração de código curto aleatório com verificação de colisão**
Ao gerar um código, a API verifica se ele já existe no banco antes de salvar, repetindo a geração em caso de colisão. A coluna `codigo_curto` também tem uma restrição `unique` no próprio banco, como camada extra de segurança.

**Containers rodando com usuário não-root**
Tanto a API quanto o worker criam um usuário de sistema dedicado (sem privilégios de login, sem diretório home) e só o utilizam após todas as etapas que exigem privilégio de root (instalação de dependências), seguindo o princípio do menor privilégio.

**Healthcheck no Postgres + `depends_on` com `condition: service_healthy`**
Um container "iniciado" não significa um serviço "pronto para uso", o Postgres pode levar alguns segundos para aceitar conexões após o container subir. Sem essa verificação ativa, API e worker poderiam tentar se conectar a um banco ainda em inicialização.

**`blpop` com timeout finito em vez de bloqueio indefinido**
Conexões de rede completamente ociosas por longos períodos podem ser derrubadas silenciosamente pela infraestrutura. Usar um timeout curto (5s) mantém a conexão ativa com verificações periódicas, tornando o worker mais resiliente.

**`try/except` no loop do worker + `restart: unless-stopped` no Compose**
Duas camadas de defesa contra falhas temporárias: o `try/except` evita que uma falha pontual (ex: timeout de rede) derrube o processo; o `restart` no Compose garante recuperação automática mesmo em falhas não previstas pelo código.

## Como rodar o projeto

Pré-requisitos: Docker e Docker Compose instalados.

```bash
docker compose up --build
```

Isso sobe os 4 containers na ordem correta, aguardando o banco de dados ficar saudável antes de iniciar API e worker.

### Testando o fluxo

Criar um link curto:
```bash
curl -X POST http://localhost:8000/encurtar \
  -H "Content-Type: application/json" \
  -d '{"url_completa": "https://www.exemplo.com"}'
```

Acessar o link curto (substitua `*****` pelo retornado acima):
```bash
curl -iL http://localhost:8000/*****
```

Verificar o processamento assíncrono do clique:
```bash
docker compose logs worker
```

## Possíveis melhorias futuras

- Migrations com Alembic, em vez de `Base.metadata.create_all`, para controle de versionamento de schema
- Autenticação e HTTPS para um cenário de produção real
- Healthcheck dedicado para o Redis
- Extrair código duplicado entre API e worker (modelo `Link`, conexão com o banco) para um módulo compartilhado
- Testes automatizados
