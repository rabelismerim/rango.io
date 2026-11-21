# rango.io

Aplicação de delivery com catálogo de restaurantes, sacola persistente e acompanhamento de pedidos. Interface em português, responsiva e com identidade visual em **preto, vermelho e amarelo**.

## Telas

### Explorar restaurantes

![Catálogo de restaurantes do rango.io](docs/images/explorar.png)

### Cardápio e sacola

| Cardápio do restaurante | Sacola de compras |
| --- | --- |
| ![Cardápio com produtos e preços](docs/images/cardapio.png) | ![Sacola com quantidade e subtotal](docs/images/sacola.png) |

### Painel do restaurante

![Painel do restaurante com gestão do cardápio](docs/images/painel.png)

### Endereço automático

<img src="docs/images/endereco.png" alt="Busca automática da rua pela localização" width="360">

### Versão mobile

<img src="docs/images/mobile.png" alt="Catálogo de restaurantes no celular" width="300">

## Funcionalidades

- Catálogo com busca, categorias, favoritos e filtros de entrega, tempo e avaliação.
- Cardápio com produtos, preços e adicionais disponíveis.
- Sacola persistente, controle de quantidades e confirmação ao trocar de restaurante.
- Login com JWT, renovação de sessão e histórico paginado de pedidos.
- Cálculo de frete com a localização do dispositivo e validação de preços no servidor.
- Acompanhamento de status por WebSocket.
- Painel do lojista para cadastrar e pausar produtos e avançar pedidos.
- PWA com manifest, ícone e cache da interface em produção.

## Tecnologias e dependências

### Ambiente

| Dependência | Uso |
| --- | --- |
| Node.js 22 e npm | Desenvolvimento e build do frontend |
| Python 3.13 e pip | Execução da API e instalação das bibliotecas |
| SQLite | Banco padrão para desenvolvimento, incluído no Python |
| PostgreSQL e Redis | Opcionais, para banco externo e processamento distribuído |
| Docker Compose | Opcional, para iniciar PostgreSQL e Redis |

### Frontend

| Biblioteca | Uso |
| --- | --- |
| Vue 3 | Interface reativa |
| Pinia 3 | Estado da sacola |
| Lucide Vue Next | Ícones |
| Vite 6 e plugin Vue 5 | Servidor de desenvolvimento e build |

### Backend

| Biblioteca | Uso |
| --- | --- |
| Django 5.2 | Aplicação, ORM e administração |
| Django REST Framework 3.16 | API REST |
| Simple JWT | Autenticação e renovação de tokens |
| drf-spectacular | Documentação OpenAPI |
| Channels e Daphne | ASGI e WebSocket |
| channels-redis | Canal de mensagens com Redis |
| Celery com Redis | Tarefas de notificação |
| psycopg | Conexão com PostgreSQL |
| dj-database-url | Configuração do banco por URL |

As fotos do catálogo são servidas pelo Unsplash; as fontes DM Sans e Manrope, pelo Google Fonts. Esses recursos precisam de conexão com a internet. A identificação da rua usa a API Photon com dados OpenStreetMap, sem bibliotecas adicionais. O servidor público é destinado a uso moderado e não garante disponibilidade; para produção com maior volume, configure uma instância própria em `VITE_PHOTON_URL` no frontend.

## Executar localmente

Os comandos abaixo usam PowerShell, na raiz do projeto.

### 1. Preparar e iniciar a API

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend/requirements.txt
$env:DEBUG='1'
.\.venv\Scripts\python backend/manage.py migrate
.\.venv\Scripts\python backend/manage.py seed
.\.venv\Scripts\python backend/manage.py runserver 127.0.0.1:8000
```

### 2. Iniciar a interface

Em outro terminal:

```powershell
cd frontend
npm ci
npm run dev -- --configLoader runner
```

Abra **http://localhost:5173**. O Vite encaminha as requisições de `/api` e `/ws` para o backend na porta 8000. A opção `configLoader runner` evita restrições de acesso do carregamento de configuração em alguns ambientes Windows.

### 3. Acessar as contas de demonstração

| Perfil | Usuário | Senha |
| --- | --- | --- |
| Cliente | `cliente` | `RangoDemo2026!` |
| Lojista | `lojista` | `RangoDemo2026!` |

Na conta do lojista, entre em **Meus pedidos → Painel do restaurante** para gerenciar produtos e pedidos. A seed está disponível apenas em desenvolvimento.

- **Documentação da API:** http://127.0.0.1:8000/api/docs/
- **Django Admin:** http://127.0.0.1:8000/admin/

Para acessar a administração, crie um usuário:

```powershell
.\.venv\Scripts\python backend/manage.py createsuperuser
```

## Fluxo de pedido

1. Selecione um restaurante e adicione produtos à sacola.
2. Informe rua e número e autorize a localização do dispositivo para calcular o frete.
3. Entre na conta e confirme o pedido.
4. Acompanhe o andamento em **Meus pedidos**.

Ao usar a localização, o Photon busca a rua mais próxima nos dados do OpenStreetMap e preenche o endereço. Confira a rua sugerida e complete o número. Se a consulta falhar, preencha o endereço manualmente. O frete continua usando as coordenadas do dispositivo. A API verifica o raio de atendimento, disponibilidade, adicionais e quantidades e recalcula o total antes de salvar o pedido.

O status segue a sequência **pendente → em preparo → saiu para entrega → entregue**. A atualização é autorizada no servidor e o WebSocket exige autenticação e vínculo com o pedido.

Sem a API, o catálogo de demonstração continua disponível; autenticação, checkout e histórico dependem do backend.

## Configuração

As variáveis devem ser definidas no ambiente do processo. O Django não carrega arquivos `.env` automaticamente.

| Variável | Descrição |
| --- | --- |
| `DEBUG` | Use `1` para desenvolvimento e `0` para produção |
| `SECRET_KEY` | Chave privada da aplicação; obrigatória em produção |
| `ALLOWED_HOSTS` | Hosts permitidos separados por vírgula |
| `DATABASE_URL` | URL do PostgreSQL; sem configuração, usa SQLite |
| `REDIS_URL` | Redis para Channels e Celery; opcional no desenvolvimento |
| `USE_POSTGIS` | Use `1` para selecionar o backend PostGIS; exige GDAL/GEOS |

### PostgreSQL e Redis opcionais

```powershell
docker compose up -d
$env:DEBUG='1'
$env:DATABASE_URL='postgres://rango:rango-local-only@localhost:5432/rango'
$env:REDIS_URL='redis://localhost:6379/0'
.\.venv\Scripts\python backend/manage.py migrate
.\.venv\Scripts\python backend/manage.py seed
.\.venv\Scripts\python backend/manage.py runserver 127.0.0.1:8000
```

Em outro terminal, com as mesmas variáveis, inicie o worker:

```powershell
cd backend
..\.venv\Scripts\celery -A config worker --pool=solo -l info
```

Sem Redis, Channels usa memória no processo ASGI e as tarefas são executadas imediatamente. Em Linux, o worker pode usar o pool padrão.

## Verificação e build

### Testes da API

```powershell
$env:DEBUG='1'
.\.venv\Scripts\python backend/manage.py test core
```

Os testes cobrem preços, adicionais, distância, disponibilidade, isolamento entre contas, transições de pedidos e autorização de WebSocket.

### Build da interface

```powershell
cd frontend
npm run build -- --configLoader runner
npm run preview -- --configLoader runner
```

O build gera `frontend/dist`. Para experimentar autenticação e pedidos, use o servidor de desenvolvimento, que já configura o proxy da API. Em produção, o servidor deve encaminhar `/api` e `/ws` para o backend.

## Arquitetura

- **Frontend:** Vue renderiza a interface; Pinia mantém a sacola no `localStorage`, e favoritos também persistem no navegador. Os tokens ficam no `sessionStorage`.
- **API:** Django REST Framework controla catálogo, autenticação, produtos e pedidos. O checkout transacional guarda os preços e adicionais no momento da compra.
- **Tempo real:** o catálogo é sincronizado a cada 15 segundos; Channels comunica as mudanças de status por WebSocket após o commit do pedido.
- **Frete:** taxa base mais distância em quilômetros multiplicada pelo preço por quilômetro, usando a fórmula de Haversine.
- **PWA:** o service worker mantém cache da interface em produção e não armazena requisições da API. A instalação depende de suporte do navegador e HTTPS ou localhost.

## Produção e escopo

Sirva `frontend/dist` por HTTPS, encaminhe `/api` e `/ws` para Daphne e configure `DEBUG=0`, `SECRET_KEY`, `ALLOWED_HOSTS`, PostgreSQL e Redis. No diretório `backend`, o servidor ASGI pode ser iniciado com:

```powershell
..\.venv\Scripts\daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

O projeto não integra pagamento real, busca de coordenadas por endereço digitado ou localização do entregador. Reconexão automática do WebSocket, idempotência de checkout e consultas espaciais indexadas são melhorias futuras.
