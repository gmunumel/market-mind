# Market Mind

Market Mind is a full-stack AI research assistant that provides real-time financial and crypto intelligence. The agent combines live DuckDuckGo market signals, a LangGraph workflow orchestrated by LangChain, Chroma vector memory, and PostgreSQL chat history to deliver contextualised investment insights with usage limits and Langfuse observability.

## Project structure

```
.
├── backend/              # FastAPI + LangChain backend (Python 3.12, uv managed)
├── frontend/             # React + Vite + Tailwind chat interface with Zustand store
├── charts/               # Helm charts for k3s deployments (frontend & backend)
├── docker-compose.yml    # Multi-service stack for local Docker workflows
├── .devcontainer/        # VS Code Dev Container definition
├── .env                  # Runtime configuration (copy-safe defaults)
└── README.md
```

## Features

- Stateful LangGraph agent using LangChain, OpenAI `gpt-4o`, DuckDuckGo search, and Chroma persistent vector store.
- PostgreSQL persistence for chat sessions and message history.
- Rate limiting per user (hourly/daily) to prevent abuse.
- Langfuse instrumentation hooks for trace monitoring.
- React chat UI with multiple conversations, dark/light themes, and Zustand-based state management.
- Dockerfiles, Docker Compose, VS Code DevContainer, and Helm charts for seamless local dev and k3s deployment.

## Prerequisites

- Python >= 3.12 with [uv](https://github.com/astral-sh/uv) (`pip install uv`).
- Node.js >= 20 and npm >= 10.
- Docker & Docker Compose (optional).
- k3s / Kubernetes cluster with Helm (optional for deployment).

## Configuration

Environment variables are managed through `.env` in the repository root. Duplicate the defaults if you need private overrides:

```bash
cp .env.example .env
```

Update the following keys before running production workloads:

- `OPENAI_API_KEY`
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
- `DATABASE_URL` (if not using Docker Compose defaults)

For local development outside Docker, set `DATABASE_URL` to your host Postgres connection string (e.g. `postgresql+psycopg://market_mind:market_mind@localhost:5432/market_mind`) and run PostgreSQL/Chroma manually or via Docker.

## Running locally (without Docker)

1. **Start dependencies (optional but recommended via Compose)**
   ```bash
   docker compose up postgres chroma
   ```

2. **Backend**
   ```bash
   cd backend
   uv sync
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Frontend**
   ```bash
   cd frontent
  npm install
   npm run dev
   ```

The chat UI is available at `http://localhost:5173` (proxied to the backend on `http://localhost:8000`). Supply an `X-User-Id` header to the backend if you integrate via API; the frontend handles this automatically.

### API quick start

- Health check: `GET http://localhost:8000/health`
- Create chat: `POST http://localhost:8000/chats`
- Send message: `POST http://localhost:8000/chats/{chatId}/messages`

## Docker workflow

Build and run the whole stack:

```bash
docker compose up --build
```

Services launched:

- `frontend` → http://localhost:5173
- `backend` → http://localhost:8000
- `postgres` (data persisted to `postgres_data` volume)
- `chroma` (vector store persisted to `chroma_data`)

Override environment variables by editing `.env` before starting Compose.

## VS Code Dev Container

1. Install the **Dev Containers** extension.
2. Open the repository in VS Code and select **Reopen in Container**.
3. The container pre-installs Python 3.12, Node 20, uv, project dependencies, and recommended extensions.

After launch:

```bash
# Backend shell
cd backend
uv run uvicorn app.main:app --reload

# Frontend shell
cd frontend
npm run dev
```

## Testing

Backend (pytest):
```bash
cd backend
uv run pytest
```

Frontend (Vitest):
```bash
cd frontend
npm run test
```

CI scripts can call these commands to validate both layers.

## Deployment to k3s with Helm

1. **Build and push images**
   ```bash
   # Backend
   docker build -t ghcr.io/<org>/market-mind-backend:latest backend
   docker push ghcr.io/<org>/market-mind-backend:latest

   # Frontend (build with API endpoint baked in)
   docker build --build-arg VITE_API_URL=http://market-mind-backend:8000 \
     -t ghcr.io/<org>/market-mind-frontend:latest frontend
   docker push ghcr.io/<org>/market-mind-frontend:latest
   ```

2. **Create a namespace and override values**
   ```bash
   kubectl create namespace market-mind
   ```
   Prepare override files (or use `--set` flags) to supply secrets safely:
   ```yaml
   # backend-values.yaml
   image:
     repository: ghcr.io/<org>/market-mind-backend
     tag: latest
   env:
     OPENAI_API_KEY: "<openai-key>"
     LANGFUSE_PUBLIC_KEY: "<langfuse-public>"
     LANGFUSE_SECRET_KEY: "<langfuse-secret>"
     DATABASE_URL: "postgresql+psycopg://market_mind:market_mind@postgresql:5432/market_mind"
   ```
   ```yaml
   # frontend-values.yaml
   image:
     repository: ghcr.io/<org>/market-mind-frontend
     tag: latest
   env:
     VITE_API_URL: "http://market-mind-backend:8000"
   ```

3. **Install the charts**
   ```bash
   helm install market-mind-backend charts/backend -n market-mind -f backend-values.yaml
   helm install market-mind-frontend charts/frontend -n market-mind -f frontend-values.yaml
   ```

4. **Verify**
   ```bash
   kubectl get pods -n market-mind
   kubectl get svc -n market-mind
   ```

The backend chart provisions a persistent volume for Chroma. Point `DATABASE_URL` at your managed PostgreSQL instance or reference an in-cluster service. For TLS/ingress, fill `ingress.hosts` and `ingress.tls` or integrate with your preferred controller (e.g., Traefik/NGINX).

## Observability & limits

- **Langfuse**: configure `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_HOST` (default cloud endpoint) to enable tracing. Without credentials the backend gracefully disables Langfuse calls.
- **Rate limiting**: defaults to 60 requests/hour and 500 requests/day per `X-User-Id`. Override with `HOURLY_REQUEST_LIMIT` / `DAILY_REQUEST_LIMIT`.

## Next steps

- Integrate authenticated user IDs to align rate limits with your identity provider.
- Automate database migrations via Alembic before deploying to production.
- Harden the Docker images (distroless, multi-stage builds) and add CI pipelines.

Happy hacking!
