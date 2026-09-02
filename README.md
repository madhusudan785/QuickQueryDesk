# QuickQueryDesk

## 1. What This Is

QuickQueryDesk is an AI-powered internal helpdesk and support ticket resolution platform designed to streamline IT, HR, Finance, and Administrative support workflows. The application enables employees to submit support tickets, automatically classifies issues by category and priority using Large Language Models (LLMs), retrieves relevant documentation from an internal knowledge base via Retrieval-Augmented Generation (RAG), and generates contextual draft replies for support agents. Support agents can review tickets, override AI classification decisions with complete audit logging, customize AI-generated draft replies, and resolve tickets with real-time status updates pushed to employees. By automating initial triage and draft generation while keeping human agents in control of final communications, QuickQueryDesk significantly reduces resolution times and improves operational efficiency for enterprise support teams.

## 2. Features Implemented

- **Authentication & Role-Based Access Control (RBAC)**
  - JWT-based authentication using PyJWT with bcrypt password hashing.
  - Role enforcement (`employee` vs. `agent`) enforced via FastAPI dependencies and database verification.
  - Strict endpoint access controls ensuring employees only view their own tickets while agents manage company-wide queues and metrics.
- **Employee Ticket Creation & Tracking**
  - Form interface for submitting support tickets with title, description, and optional attachment filename.
  - Employee dashboard (`/dashboard`) displaying submitted tickets with status indicators, categories, priorities, and final resolutions.
  - Live status tracking of submitted tickets (`/tickets/:id`).
- **AI-Powered Ticket Classification**
  - Direct integration with Groq (`groq/compound-mini`) and Google Gemini APIs.
  - Automatic classification of tickets into 5 standard categories (`IT`, `HR`, `Finance`, `Admin`, `Other`) and 3 priority levels (`Low`, `Medium`, `High`).
  - Structured JSON output schema enforcement with automatic fallback defaults (`Other`, `Medium`) if the LLM call fails or returns unparseable data.
- **RAG Knowledge Base Retrieval**
  - Knowledge base built from markdown articles stored in [`backend/knowledge_base/*.md`](file:///d:/quickquerydesk-/backend/knowledge_base).
  - Document chunking using LangChain `RecursiveCharacterTextSplitter` (chunk size: 800, overlap: 100).
  - Dense vector embeddings generated via `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional normalized vectors).
  - In-memory vector store indexing using `FAISS` with Maximum Inner Product similarity matching (cosine similarity).
  - Top-k relevance retrieval ($k=3$) with strict relevance score thresholding ($0.3$) to prevent weak or irrelevant matches.
- **AI-Generated Draft Replies**
  - Automatic generation of draft replies grounded in retrieved knowledge base articles using Groq/Gemini LLMs.
  - Strict instruction prompt engineering to produce direct, actionable, step-by-step troubleshooting instructions.
  - Automated post-processing cleanup to sanitize raw markdown bracket artifacts and redundant link formatting.
  - Agent-facing UI on ticket detail view allowing agents to review, edit, or replace the draft before sending to the employee.
- **Agent Dashboard & Management**
  - Queue view of all support tickets (`/agent/dashboard`) with real-time statistics (open/resolved counts).
  - Server-side filtering by status (`open`, `resolved`), category, priority, and text search across titles.
  - Detailed ticket management view (`/agent/tickets/:id`) displaying original ticket details, employee information, AI suggestions, and RAG sources.
- **Classification Overrides & Audit Logging**
  - Capability for agents to override AI-suggested category and priority values.
  - Immutable storage of original AI predictions (`ai_category`, `ai_priority`) alongside active current values (`current_category`, `current_priority`).
  - Automated audit log generation (`AuditLog` model) recording modified fields, previous values, updated values, acting agent ID, and timestamps.
  - Detailed audit history UI timeline on the agent ticket detail view.
- **Semantic Caching**
  - In-memory vector similarity cache (`SemanticVectorCache`) for query deduplication.
  - Computes cosine similarity against cached query embeddings; queries matching with similarity $\ge 0.88$ return cached category, priority, draft reply, and RAG sources in $<15\text{ms}$ with zero LLM API cost.
- **Background AI Processing**
  - Async task offloading via FastAPI `BackgroundTasks`.
  - Immediate synchronous ticket creation and classification response followed by asynchronous execution of RAG retrieval and draft generation.
  - Agent notifications dispatched via WebSockets (`ticket_ai_ready`) once background processing completes.
- **Rate Limiting**
  - In-memory sliding window rate limiter (`SlidingWindowRateLimiter`).
  - Restricts ticket creation to a maximum of 2 tickets per 12 hours per employee user to prevent spam and LLM resource exhaustion.
- **WebSocket Real-Time Updates**
  - Native FastAPI WebSockets at `/ws/agent` and `/ws/employee`.
  - Query parameter JWT authentication (`?token=...`) with role validation prior to WebSocket connection acceptance.
  - Real-time event broadcasting: `ticket_created` to all agents, `ticket_ai_ready` to agents, and `ticket_resolved` to the specific ticket creator.
  - Frontend auto-reconnection service (`WebSocketService`) with exponential backoff (1s to 30s, capped at 10 attempts).
- **Metrics & Analytics Dashboard**
  - Dedicated agent analytics dashboard (`/agent/metrics`) with visual charts powered by Recharts.
  - Computes total ticket count, status breakdown (Open vs. Resolved), category distribution across standard categories, median resolution time in hours, and AI category override percentage (`total_overridden / total_classified * 100`).

## 3. Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend Framework** | React 19 (`react`, `react-dom`) | User interface component architecture |
| **Frontend Build Tool** | Vite 8 (`vite`) | Development server and module bundler |
| **Frontend Routing** | React Router v7 (`react-router-dom`) | Client-side page navigation and route protection |
| **Styling & UI** | Tailwind CSS v4 (`@tailwindcss/vite`), Lucide React | Modern utility styling and icon set |
| **Data Visualization** | Recharts (`recharts`) | Interactive charts on the Agent Metrics Dashboard |
| **HTTP Client** | Axios (`axios`) | REST API communication with backend |
| **Backend Framework** | FastAPI 0.115 (`fastapi`) | High-performance asynchronous REST and WebSocket API |
| **ASGI Server** | Uvicorn 0.34 (`uvicorn[standard]`) | Asynchronous server supporting HTTP and WebSockets |
| **Database & ORM** | PostgreSQL, SQLAlchemy 2.0 (`sqlalchemy[asyncio]`), asyncpg | Asynchronous relational data storage and Object-Relational Mapping |
| **Database Migrations** | Alembic 1.16 (`alembic`), psycopg2-binary | Database schema migrations and sync connection handling |
| **Authentication & Security** | PyJWT (`pyjwt`), bcrypt (`bcrypt`), HTTPBearer | Passwords hashing, JWT token issue/validation, and RBAC |
| **LLM Providers** | Groq SDK (`groq`), Google GenAI SDK (`google-genai` / `google-generativeai`) | Ticket classification and draft reply generation |
| **RAG & Vector Search** | LangChain 0.3 (`langchain`), FAISS (`faiss-cpu`), Sentence-Transformers (`sentence-transformers/all-MiniLM-L6-v2`) | Knowledge base loading, text chunking, dense vector embeddings, and similarity search |
| **Data Validation** | Pydantic v2 (`pydantic`), Pydantic Settings (`pydantic-settings`) | Schema validation, type safety, and environment setting parsing |
| **Testing** | Pytest 8.3 (`pytest`, `pytest-asyncio`), HTTPX (`httpx`), asyncpg | Unit, integration, and API testing |

## 4. Architecture

```mermaid
flowchart TD
    subgraph Client ["Frontend (React 19 + Vite)"]
        UI[Employee & Agent UI]
        WSClient[WebSocketService / useWebSocket]
    end

    subgraph API ["FastAPI Backend"]
        Router[API Gateway / APIRouter]
        AuthDep[JWT Security & RBAC Dependencies]
        RateLimiter[SlidingWindowRateLimiter]
        WSManager[WebSocket ConnectionManager]
        BGTasks[BackgroundTasks Queue]
    end

    subgraph Data ["Data & Caching"]
        DB[(PostgreSQL Database)]
        SemCache[SemanticVectorCache]
    end

    subgraph AI ["AI & RAG Pipeline"]
        LLM[Groq / Gemini LLM API]
        RAGEngine[RAG Engine]
        Embeddings[Sentence-Transformers all-MiniLM-L6-v2]
        FAISSIndex[(FAISS Vector Store)]
        KBFiles[Knowledge Base *.md Files]
    end

    UI -->|HTTP Requests| Router
    WSClient <-->|WebSocket Stream /ws/agent & /ws/employee| WSManager

    Router --> AuthDep
    Router --> RateLimiter
    Router --> SemCache

    Router -->|Sync Classify| LLM
    Router -->|Save Ticket| DB
    Router -->|Enqueue RAG| BGTasks

    BGTasks -->|Retrieve Context| RAGEngine
    RAGEngine --> Embeddings
    Embeddings --> FAISSIndex
    KBFiles -->|Startup Load| FAISSIndex

    BGTasks -->|Generate Draft| LLM
    BGTasks -->|Update Draft & Sources| DB
    BGTasks -->|Cache Query & Response| SemCache
    BGTasks -->|Notify Completion| WSManager
    Router -->|Notify Event| WSManager
```

### Ticket Flow Through the System

1. **Submission & Rate Limiting**: An employee submits a ticket (`POST /tickets`). The backend validates the JWT token, checks the user's role, and evaluates the `SlidingWindowRateLimiter` (max 2 tickets per 12 hours).
2. **Semantic Cache Evaluation**: The system generates a vector embedding for the query (`title + description`) and queries the `SemanticVectorCache`. If a query with cosine similarity $\ge 0.88$ exists, the cached classification, draft reply, and RAG sources are immediately assigned ($<15\text{ms}$, 0 LLM tokens).
3. **Synchronous Classification**: On a cache miss, the backend calls the LLM (Groq or Gemini) synchronously to classify the category (`IT`, `HR`, `Finance`, `Admin`, `Other`) and priority (`Low`, `Medium`, `High`) using a structured JSON schema. If classification fails or no API key is provided, safe defaults (`Other`, `Medium`) are assigned.
4. **Database Persistence & Initial Event**: The ticket record is saved to PostgreSQL with `ai_category` and `ai_priority` populated. An initial WebSocket notification (`ticket_created`) is broadcast to connected agents.
5. **Asynchronous RAG & Draft Generation**: FastAPI spawns a background task (`BackgroundTasks`) to perform RAG retrieval against the FAISS vector store (top-3 articles with score $\ge 0.3$). The retrieved context is formatted into a prompt sent to the LLM to generate a concise draft reply.
6. **Draft Completion & Agent Alert**: The draft reply and RAG sources are written back to PostgreSQL, cached in the `SemanticVectorCache`, and a `ticket_ai_ready` WebSocket event is dispatched to agents.
7. **Agent Review & Overrides**: An agent views the ticket on the Agent Dashboard (`/agent/tickets/:id`). If the agent changes the category or priority (`PATCH /tickets/{id}`), an `AuditLog` entry is created recording the old value, new value, agent ID, and timestamp.
8. **Resolution & Notification**: The agent edits or accepts the AI draft reply and submits it (`POST /tickets/{id}/reply`). The ticket status changes to `resolved`, `resolved_at` and `resolved_by` are set, and a `ticket_resolved` WebSocket message is pushed to the specific employee, causing their dashboard to update live.

## 5. Project Structure

```text
QuickQueryDesk/
├── backend/
│   ├── alembic/                      # Alembic database migration scripts
│   │   ├── versions/                 # Migration version files (0001_initial_users, 0002_add_tickets)
│   │   └── env.py                    # Alembic migration configuration
│   ├── app/
│   │   ├── api/                      # FastAPI router modules
│   │   │   ├── auth.py               # /auth/register, /auth/login
│   │   │   ├── tickets.py            # /tickets CRUD, overrides, replies, audit logs
│   │   │   └── metrics.py            # /metrics agent analytics endpoint
│   │   ├── core/                     # Application core infrastructure
│   │   │   ├── config.py             # Pydantic environment configuration Settings
│   │   │   ├── dependencies.py       # FastAPI auth & role dependencies (require_role)
│   │   │   ├── rate_limiter.py       # SlidingWindowRateLimiter (2 tickets / 12h)
│   │   │   └── security.py           # Bcrypt hashing & JWT encode/decode functions
│   │   ├── database/                 # Database configuration
│   │   │   ├── base.py               # SQLAlchemy DeclarativeBase
│   │   │   └── session.py            # Async SQLAlchemy engine & session factory
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   ├── user.py               # User model (id, email, password_hash, role)
│   │   │   ├── ticket.py             # Ticket model (AI & current category/priority, status)
│   │   │   └── audit_log.py          # AuditLog model (ticket_id, agent_id, field, values)
│   │   ├── rag/                      # RAG & Vector Search Pipeline
│   │   │   ├── engine.py             # FAISS index, embeddings, similarity search, startup pre-warming
│   │   │   ├── knowledge_base.py     # DirectoryLoader for backend/knowledge_base/*.md
│   │   │   └── semantic_cache.py     # SemanticVectorCache (similarity threshold 0.88)
│   │   ├── schemas/                  # Pydantic data schemas
│   │   │   ├── auth.py, ticket.py, audit_log.py, metrics.py, user.py
│   │   ├── services/                 # Business logic services
│   │   │   └── llm.py                # Groq / Gemini API client, classification & draft prompts
│   │   ├── websocket/                # Real-time WebSocket infrastructure
│   │   │   └── manager.py            # ConnectionManager for agent & employee pools
│   │   └── main.py                   # FastAPI app entry point, lifespan, CORS & WS endpoints
│   ├── knowledge_base/               # Knowledge base source markdown documents (8 articles)
│   │   ├── vpn_setup.md, password_reset.md, expense_reimbursement.md, ...
│   ├── tests/                        # Automated backend test suite
│   │   ├── conftest.py, test_llm.py, test_metrics.py, test_security.py
│   ├── .env.example                  # Environment configuration template
│   ├── alembic.ini                   # Alembic configuration file
│   ├── docker-entrypoint.sh          # Docker: wait for DB, run migrations, start app
│   ├── Dockerfile                    # Docker: backend container image
│   └── requirements.txt              # Python dependencies specification
├── frontend/
│   ├── src/
│   │   ├── components/               # Reusable UI components
│   │   │   └── layout/               # Navbar, ProtectedRoute
│   │   ├── context/                  # AuthContext React state provider
│   │   ├── hooks/                    # Custom React hooks (useWebSocket)
│   │   ├── pages/                    # React page views
│   │   │   ├── Login.tsx, Register.tsx
│   │   │   ├── EmployeeDashboard.tsx, CreateTicket.tsx, EmployeeTicketDetail.tsx
│   │   │   ├── AgentDashboard.tsx, AgentTicketDetail.tsx, MetricsDashboard.tsx
│   │   ├── services/                 # API & WebSocket client services
│   │   │   ├── api.ts, auth.ts, tickets.ts, websocket.ts
│   │   ├── types/                    # TypeScript interfaces & type definitions
│   │   ├── App.tsx                   # Main React app component & route definitions
│   │   └── main.tsx                  # React entry point
│   ├── package.json                  # Frontend dependencies & scripts
│   ├── tsconfig.json                 # TypeScript compiler configuration
│   ├── vite.config.ts                # Vite dev server & API proxy configuration
│   ├── nginx.conf                    # Docker: nginx reverse proxy & SPA serving config
│   └── Dockerfile                    # Docker: frontend container image (multi-stage)
├── docker-compose.yml                # Docker Compose: full-stack orchestration
├── .env.docker.example               # Docker: environment variables template
├── export_project_to_md.py           # Helper utility to export project context
└── README.md                         # Root project documentation
```

## 6. How to Run Locally

### Prerequisites

Ensure you have the following software installed on your system:
- **Python**: Version `3.11` or `3.12` (Python 3.10+ required)
- **Node.js**: Version `18.x` or `20.x`+ and `npm`
- **PostgreSQL**: Version `14` or higher running locally or accessible via network

---

### Step 1: Clone the Repository

```powershell
git clone https://github.com/madhusudan785/QuickQueryDesk.git
cd QuickQueryDesk
```

---

### Step 2: Backend Setup

1. **Navigate to the backend directory**:
   ```powershell
   cd backend
   ```

2. **Create and activate a Python virtual environment**:
   - **Windows PowerShell**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Python dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Copy the example environment file to `.env`:
   - **Windows PowerShell**:
     ```powershell
     Copy-Item .env.example .env
     ```
   - **Linux / macOS**:
     ```bash
     cp .env.example .env
     ```
   Edit `.env` to configure your PostgreSQL connection string and LLM API key (see [Environment Variables](#7-environment-variables)).

5. **Set Up PostgreSQL Database**:
   Create a database in PostgreSQL named `quickquerydesk` (or matching your `DATABASE_URL`):
   ```sql
   CREATE DATABASE quickquerydesk;
   ```

6. **Run Database Migrations**:
   Apply Alembic migrations to create the required tables (`users`, `tickets`, `audit_logs`):
   ```powershell
   alembic upgrade head
   ```

7. **Start the Backend Server**:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```
   The backend server will start at `http://localhost:8000`. You can view the API documentation at `http://localhost:8000/docs`.

---

### Step 3: Frontend Setup

1. **Open a new terminal and navigate to the frontend directory**:
   ```powershell
   cd frontend
   ```

2. **Install Node dependencies**:
   ```powershell
   npm install
   ```

3. **Start the Frontend Development Server**:
   ```powershell
   npm run dev
   ```
   The frontend application will boot at `http://localhost:5173`. The Vite development server automatically proxies backend requests (`/auth`, `/tickets`, `/metrics`, `/ws`) to `http://localhost:8000`.

---

## 7. Run with Docker

QuickQueryDesk includes a complete Docker Compose setup to start the entire stack (PostgreSQL + FastAPI backend + React frontend) with a single command.

### Prerequisites

- [Docker](https://www.docker.com/get-started) (v20+ recommended)
- [Docker Compose](https://docs.docker.com/compose/) (included with Docker Desktop on Windows/macOS)

### Configure Environment Variables

1. Copy the Docker-specific environment template to a `.env` file **in the project root**:
   - **Windows PowerShell**:
     ```powershell
     Copy-Item .env.docker.example .env
     ```
   - **Linux / macOS**:
     ```bash
     cp .env.docker.example .env
     ```

2. Edit `.env` to configure your LLM API key (optional) and set a production-safe `JWT_SECRET`:
   ```dotenv
   LLM_API_KEY=gsk_your_groq_key_here
   JWT_SECRET=a-strong-random-secret
   ```
   > If `LLM_API_KEY` is left blank, the application runs in graceful fallback mode with template-based classification and draft replies.

### Start the Application

```bash
docker compose up --build
```

This command:
1. Starts a **PostgreSQL 16** container with persistent data volume.
2. Builds and starts the **FastAPI backend** container, waits for PostgreSQL to be healthy, runs Alembic database migrations automatically, initializes the RAG engine (embedding model + FAISS vector index), and starts uvicorn on port `8000`.
3. Builds the **React frontend** as static assets and serves them via **nginx** on port `3000`, with automatic reverse proxying of API requests (`/auth`, `/tickets`, `/metrics`) and WebSocket connections (`/ws/`) to the backend container.

### Access the Application

| Service | URL |
|---------|-----|
| **Frontend (UI)** | [http://localhost:3000](http://localhost:3000) |
| **Backend API Docs** | [http://localhost:3000/docs](http://localhost:3000/docs) |
| **Backend Direct** | [http://localhost:8000](http://localhost:8000) |
| **PostgreSQL** | `localhost:5433` (mapped to avoid host conflict) |

Register an **Employee** account on the UI to submit tickets, and a separate **Agent** account to access the Agent Dashboard and Metrics.

### Docker Services Overview

| Service | Image / Build | Port | Purpose |
|---------|---------------|------|---------|
| `db` | `postgres:16-alpine` | `5433:5432` | PostgreSQL database with named volume |
| `backend` | Built from `backend/Dockerfile` | `8000:8000` | FastAPI + Uvicorn + Alembic migrations |
| `frontend` | Built from `frontend/Dockerfile` | `3000:80` | nginx serving React SPA + API/WS reverse proxy |

### Stop Containers

```bash
docker compose down
```

### Stop and Remove Database Data

To remove all containers **and** the persistent PostgreSQL volume:

```bash
docker compose down -v
```

> ⚠️ **Note**: The repository does not contain a database seed script. After starting the application via Docker, you must register user accounts through the frontend UI (`/register`). Select role **Employee** to submit tickets, or role **Agent** to access the agent dashboard, ticket management, and metrics.

---

## 8. Environment Variables

Environment variables are managed in [`backend/.env`](file:///d:/quickquerydesk-/backend/.env) (created from [`backend/.env.example`](file:///d:/quickquerydesk-/backend/.env.example)).

| Variable | Required | Description | Default / Example |
|----------|----------|-------------|-------------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string using `postgresql+asyncpg://` driver | `postgresql+asyncpg://postgres:postgres@localhost:5432/quickquerydesk` |
| `JWT_SECRET` | Yes | Secret key used to sign JWT authentication tokens | `change-me-in-production` |
| `JWT_ALGORITHM` | No | Cryptographic algorithm for JWT signing | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token expiration time in minutes | `60` |
| `FRONTEND_URL` | No | Allowed CORS origin for frontend application | `http://localhost:5173` |
| `LLM_API_KEY` | Optional | API Key for Groq or Google Gemini | `gsk_...` (Groq) or `AIza...` (Gemini) |
| `LLM_MODEL` | No | Target model name for classification and draft replies | `groq/compound-mini` or `gemini-2.5-flash` |

### LLM API Configuration Notes

- **Groq API Key**: If using Groq, obtain a free API key at [Groq Console](https://console.groq.com/keys) and set `LLM_API_KEY=gsk_...` and `LLM_MODEL=groq/compound-mini` (or `llama-3.3-70b-versatile`).
- **Google Gemini API Key**: If using Gemini, obtain an API key from [Google AI Studio](https://aistudio.google.com/apikey) and set `LLM_API_KEY=AIza...` and `LLM_MODEL=gemini-2.5-flash`.
- **Graceful Fallback Mode**: If `LLM_API_KEY` is left blank or set to a placeholder, QuickQueryDesk automatically operates in fallback mode. Tickets will be assigned fallback routing defaults (`category=Other`, `priority=Medium`), RAG retrieval will still search the knowledge base, and a structured template fallback draft reply will be generated without throwing errors or crashing.

---

## 9. Database and Sample Data

### Database Schema Creation

Database tables are initialized using Alembic migrations:
- **Migration `0001_initial_users.py`**: Creates the `users` table storing user credentials, role (`employee` or `agent`), and creation timestamps.
- **Migration `0002_add_tickets_and_audit_logs.py`**: Creates the `tickets` table (storing original AI suggestions, current overridden values, status, AI draft, final reply, RAG sources JSON) and the `audit_logs` table (tracking agent overrides).

---

> ⚠️ **Current implementation limitation**: The repository does NOT currently contain a dedicated standalone database seed script or CLI command (e.g. `seed.py`) to automatically generate sample employee/agent accounts or mock support tickets upon deployment. (Note: Automated test data generation is implemented internally within [`backend/tests/test_metrics.py`](file:///d:/quickquerydesk-/backend/tests/test_metrics.py) for testing purposes).

### Recommendation for Seed Script Addition

To enable immediate out-of-the-box manual testing by new developers, a seed script (e.g. `backend/app/database/seed.py`) should be added to populate:
1. **Sample Employee Account**: `employee@example.com` / `Password123!` (Role: `employee`)
2. **Sample Support Agent Account**: `agent@example.com` / `Password123!` (Role: `agent`)
3. **Sample Tickets**: A set of open and resolved tickets across IT, HR, and Finance categories with historical audit logs.

Currently, developers running the app for the first time should register a new account on the UI (`/register`) as an **Employee** to submit tickets, and register a separate account as an **Agent** to access the Agent Dashboard and Metrics.

---

## 10. API Endpoints

All REST routes are defined in [`backend/app/api/`](file:///d:/quickquerydesk-/backend/app/api).

| Method | Endpoint | Purpose | Authentication | Allowed Role |
|--------|----------|---------|----------------|--------------|
| `GET` | `/health` | Application health check endpoint | None | Public |
| `POST` | `/auth/register` | Register a new employee or agent user account | None | Public |
| `POST` | `/auth/login` | Authenticate credentials and receive JWT bearer token | None | Public |
| `POST` | `/tickets` | Submit a new support ticket (rate-limited, triggers classification & RAG) | Bearer JWT | `employee` |
| `GET` | `/tickets/my` | Retrieve all support tickets submitted by the authenticated employee | Bearer JWT | `employee` |
| `GET` | `/tickets` | Retrieve all support tickets with filtering (`status`, `category`, `priority`, `search`) | Bearer JWT | `agent` |
| `GET` | `/tickets/{id}` | Retrieve full details of a specific ticket | Bearer JWT | `employee` (own) / `agent` |
| `PATCH` | `/tickets/{id}` | Override ticket category or priority (creates `AuditLog` entry) | Bearer JWT | `agent` |
| `POST` | `/tickets/{id}/reply` | Submit final resolution reply and mark ticket as `resolved` | Bearer JWT | `agent` |
| `GET` | `/tickets/{id}/audit` | Retrieve complete audit log history for a ticket's overrides | Bearer JWT | `agent` |
| `GET` | `/metrics` | Retrieve aggregated ticket, resolution time, and AI override analytics | Bearer JWT | `agent` |
| `WS` | `/ws/agent` | WebSocket stream for real-time agent notifications (`ticket_created`, `ticket_ai_ready`) | Query Param `?token=...` | `agent` |
| `WS` | `/ws/employee` | WebSocket stream for real-time employee updates (`ticket_classified`, `ticket_resolved`) | Query Param `?token=...` | `employee` |

---

## 11. AI and RAG Pipeline

The RAG (Retrieval-Augmented Generation) and AI pipeline is implemented across [`backend/app/rag/`](file:///d:/quickquerydesk-/backend/app/rag) and [`backend/app/services/llm.py`](file:///d:/quickquerydesk-/backend/app/services/llm.py).

```text
Incoming Ticket Query (Title + Description)
    │
    ├── 1. Semantic Cache Check (SemanticVectorCache)
    │      ├── HIT (Cosine Sim >= 0.88) ──> Return Cached Classification & Draft (<15ms, 0 Tokens)
    │      └── MISS ───────────────────────> Continue to Step 2
    │
    ├── 2. Single-Attempt LLM Classification (classify_ticket)
    │      ├── Call Groq / Gemini API with JSON Schema (Category & Priority)
    │      └── On Failure ─────────────────> Fallback to ("Other", "Medium")
    │
    ├── 3. Save Ticket to DB & Dispatch 'ticket_created' WS Event to Agents
    │
    └── 4. Asynchronous Background Task (_generate_draft_background)
           ├── Vector Search: Embed query with sentence-transformers/all-MiniLM-L6-v2
           ├── FAISS Retrieval: Top-3 chunks matching score_threshold >= 0.3
           ├── Format RAG Context String from Markdown Knowledge Base
           ├── Call LLM to Generate Actionable Step-by-Step Draft Reply
           ├── Post-Process: Clean Markdown Link Artifacts & Syntax
           ├── Cache Query Vector & Payload in SemanticVectorCache
           └── Update Ticket in DB & Dispatch 'ticket_ai_ready' WS Event to Agents
```

### Detailed Pipeline Components

1. **Document Loading**: On startup, [`knowledge_base.py`](file:///d:/quickquerydesk-/backend/app/rag/knowledge_base.py) uses LangChain's `DirectoryLoader` and `TextLoader` to load all 8 markdown files in [`backend/knowledge_base/`](file:///d:/quickquerydesk-/backend/knowledge_base). The article title is parsed from the first level-1 markdown header (`# Title`).
2. **Text Chunking**: Documents are split using `RecursiveCharacterTextSplitter` with `chunk_size=800` characters and `chunk_overlap=100` characters, producing 24 granular chunks.
3. **Embedding Generation**: Chunks are embedded using `sentence-transformers/all-MiniLM-L6-v2` via `HuggingFaceEmbeddings` with normalized output vectors (384 dimensions).
4. **Vector Store Construction**: An in-memory `FAISS` vector store is populated using `DistanceStrategy.MAX_INNER_PRODUCT` to enable fast exact cosine similarity matching.
5. **Startup Pre-Warming**: In [`main.py`](file:///d:/quickquerydesk-/backend/app/main.py), FastAPI's `lifespan` handler executes `async_initialize_rag()` at boot, pre-loading the embedding model and FAISS index in a background thread to eliminate first-request latency.
6. **Relevant Document Retrieval**: `retrieve_relevant_articles(query, top_k=3, score_threshold=0.3)` performs similarity search. Chunks below score threshold 0.3 are discarded to prevent hallucination.
7. **Ticket Classification**: `classify_ticket()` formats title and description into `CLASSIFICATION_PROMPT` and invokes Groq/Gemini with strict JSON schema constraints. Results are validated against allowed categories (`IT`, `HR`, `Finance`, `Admin`, `Other`) and priorities (`Low`, `Medium`, `High`).
8. **Draft Reply Generation**: `generate_draft_reply_ext()` combines retrieved KB context with ticket details. The LLM is instructed to skip greetings/fluff and output numbered, actionable steps with plain text URLs.
9. **Fallback Handling**: If an LLM call times out, fails, or no API key is provided, `_create_fallback_draft()` generates a structured template response incorporating retrieved KB snippets.
10. **Semantic Caching**: `SemanticVectorCache` computes cosine similarity against historical query embeddings. Matches with score $\ge 0.88$ return cached results instantly.

---

## 12. Real-Time Updates

Real-time updates are implemented via native WebSockets in [`backend/app/websocket/manager.py`](file:///d:/quickquerydesk-/backend/app/websocket/manager.py) and consumed in the frontend via [`frontend/src/services/websocket.ts`](file:///d:/quickquerydesk-/frontend/src/services/websocket.ts).

### Architecture & Endpoints

- **`/ws/agent`**: Dedicated endpoint for connected agents. Connected agents receive broadcasting events when any employee creates a new ticket (`ticket_created`) or when background AI draft generation finishes (`ticket_ai_ready`).
- **`/ws/employee`**: Dedicated endpoint for employees. Connected employees receive targeted status events (`ticket_classified`, `ticket_resolved`) for their specific filed tickets.

### Authentication

Because standard browser WebSocket APIs do not support custom request headers, authentication tokens are passed as a URL query parameter (`?token=<JWT_TOKEN>`). Prior to calling `websocket.accept()`, the backend decodes the JWT token and verifies the user's role. Invalid or missing tokens result in immediate connection rejection with WebSocket closure code `1008 (Policy Violation)`.

### Frontend Reconnection Strategy

The frontend `WebSocketService` automatically handles connection dropouts:
- **Exponential Backoff**: Reconnection delays scale exponentially ($1\text{s}, 2\text{s}, 4\text{s}, 8\text{s}, \dots, 30\text{s}$).
- **Attempt Cap**: Capped at a maximum of 10 reconnection attempts.
- **REST Fallback**: REST endpoints remain the single source of truth; if a WebSocket message is missed during a network hiccup, the UI re-syncs state on page navigation or manual refresh.

---

## 13. Metrics Dashboard

The Agent Metrics Dashboard ([`frontend/src/pages/MetricsDashboard.tsx`](file:///d:/quickquerydesk-/frontend/src/pages/MetricsDashboard.tsx)) visualizes operational performance metrics fetched from `GET /metrics` ([`backend/app/api/metrics.py`](file:///d:/quickquerydesk-/backend/app/api/metrics.py)).

### Calculated Analytics

1. **Status Counts**: Total open vs. resolved tickets computed via SQL `GROUP BY status`.
2. **Category Distribution**: Counts of tickets across `IT`, `HR`, `Finance`, `Admin`, and `Other` computed via SQL `GROUP BY current_category`.
3. **Median Resolution Time**: Calculated in Python using `statistics.median()` over the duration `(resolved_at - created_at)` in hours for all resolved tickets. Returns `null` if no tickets have been resolved.
4. **AI Category Override Percentage**: Computed directly in PostgreSQL using conditional aggregation:
   $$\text{Override Percentage} = \frac{\text{Total Overridden Tickets}}{\text{Total Classified Tickets}} \times 100$$
   where an override is identified when `ai_category IS NOT NULL` and `current_category != ai_category`.

### Access Control

The endpoint enforces strict agent role authorization using `Depends(require_role("agent"))`. Attempts by employees or unauthenticated requests return `HTTP 403 Forbidden`.

---

## 14. Background Processing and Rate Limiting

### Asynchronous Background AI Processing

Ticket creation calls LLM classification synchronously to immediately confirm ticket category to the user. However, RAG context retrieval and draft reply generation can take 1–3 seconds depending on LLM latency. To maintain low API latency ($<200\text{ms}$ response time), QuickQueryDesk offloads RAG retrieval and draft generation to FastAPI's `BackgroundTasks`. Once complete, the background worker updates the database record and alerts connected agents over WebSockets (`ticket_ai_ready`).

### Rate Limiting

To prevent API abuse and control LLM token consumption, ticket creation is protected by an in-memory sliding window rate limiter ([`backend/app/core/rate_limiter.py`](file:///d:/quickquerydesk-/backend/app/core/rate_limiter.py)):
- **Limit**: Maximum **2 tickets per 12 hours** per employee user.
- **Enforcement**: Timestamps of ticket creation attempts are stored per user ID. Requests exceeding the limit raise `HTTP 429 Too Many Requests`.

---

## 15. Testing

The backend test suite is located in [`backend/tests/`](file:///d:/quickquerydesk-/backend/tests) and uses `pytest` and `httpx`.

### Running Tests

1. **Activate the virtual environment**:
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   ```

2. **Run all backend unit & integration tests**:
   ```powershell
   pytest tests/ -v
   ```

3. **Run the RAG retrieval verification script**:
   ```powershell
   python test_rag.py
   ```

### Test Coverage Summary

- **[`test_llm.py`](file:///d:/quickquerydesk-/backend/tests/test_llm.py)**:
  - JSON classification output parsing and markdown stripping.
  - LLM fallback handling when invalid JSON or non-JSON responses are returned.
  - Serialization of RAG search results (`relevance_score` as float).
  - Fallback draft reply generation with and without RAG context.
  - Mocked LLM classification and draft generation success/failure paths.
  - Strict Pydantic input schema validation.
  - RAG engine singleton initialization and reuse.
  - Sensitive log filter token redaction (`token=[REDACTED]`).
- **[`test_metrics.py`](file:///d:/quickquerydesk-/backend/tests/test_metrics.py)**:
  - Authentication and role checking on `GET /metrics` (unauthenticated 403, employee 403, agent 200).
  - Database aggregation of status counts and category distributions via raw `asyncpg`.
  - Median resolution hours calculation logic.
  - AI category override percentage computation.
- **[`test_security.py`](file:///d:/quickquerydesk-/backend/tests/test_security.py)**:
  - Password hashing and verification using `bcrypt`.
  - JWT access token generation and payload decoding.
  - Expired JWT token validation handling (`ExpiredSignatureError`).

---

## 16. Decisions and Tradeoffs

1. **JWT in Query Parameters for WebSockets**: Browser native `WebSocket` APIs do not support custom headers. Passing the JWT in the query string (`/ws/agent?token=...`) allows authentication before connection acceptance. To mitigate security risks, a custom logging filter (`SensitiveDataFilter`) automatically redacts token values from all server logs.
2. **Immutable AI Suggestions vs. Overridable Current Values**: QuickQueryDesk maintains separate database columns for initial AI suggestions (`ai_category`, `ai_priority`) and current values (`current_category`, `current_priority`). This architectural decision enables accurate calculation of AI override metrics over time without losing initial AI predictions.
3. **Single-Attempt LLM Execution with Graceful Degradation**: Rather than retrying failed LLM calls in a loop (which increases latency and cost), the system executes a single constrained attempt. If the call fails or returns unparseable output, it immediately falls back to default values (`Other`, `Medium`) and template draft generation.
4. **Local FAISS Vector Index over External Vector DB**: Using an in-memory `FAISS` index with `sentence-transformers/all-MiniLM-L6-v2` eliminates external cloud dependencies (e.g., Pinecone, Qdrant), ensuring fast local retrieval (<10ms) and simple local deployment.
5. **In-Memory Semantic Cache & Rate Limiter**: The sliding window rate limiter and semantic vector cache are stored in process memory. This keeps setup simple with zero third-party infrastructure requirements, with the accepted tradeoff that state resets if the backend server restarts.
6. **Native WebSockets over Socket.io**: Native FastAPI WebSockets provide lightweight push notifications without adding heavy client/server libraries or room management overhead.

---

## 17. What I Would Do With More Time

- **Distributed Caching & Rate Limiting**: Replace in-memory rate limiting and semantic caching with **Redis** to ensure state persists across server restarts and scales horizontally across multiple backend worker processes.
- **Persistent Distributed Vector Database**: Replace local FAISS with **pgvector** (PostgreSQL extension) or a vector database like **Qdrant** / **Milvus** to allow dynamic knowledge base updates without rebuilding in-memory indexes.
- **Production Background Worker Queue**: Replace FastAPI `BackgroundTasks` with a dedicated task queue (such as **Celery** or **ARQ**) backed by Redis/RabbitMQ for robust task retries and worker monitoring.
- **Production Seed & Fixture CLI**: Create a CLI script (`python -m app.database.seed`) to populate realistic employee, agent, ticket, and audit log data automatically.
- **File Attachment Storage**: Implement cloud object storage (e.g. AWS S3, Azure Blob Storage) for handling ticket file uploads instead of storing file names.
- **CI/CD Pipelines**: Add GitHub Actions workflows for automated testing, linting, Docker image building, and deployment.
- **Comprehensive RAG Evaluation**: Implement automated RAG evaluation metrics (e.g. using Ragas or TruLens) to measure context precision, recall, and faithfulness.

---

## 18. Known Issues and Limitations

- **In-Memory Volatility**: The `SlidingWindowRateLimiter` and `SemanticVectorCache` store state in process memory. Restarting the backend server resets active rate limits and clears cached semantic embeddings.
- **Single-Process WebSocket Scaling**: The WebSocket `ConnectionManager` manages connections in-memory. In a multi-worker production environment (e.g. Uvicorn with multiple workers or Kubernetes pods), WebSockets require a shared pub/sub message broker (such as Redis Pub/Sub) to broadcast events across instances.
- **Knowledge Base Index Rebuilding**: The FAISS vector store is constructed in memory at startup. Adding or updating markdown articles in `backend/knowledge_base/` requires restarting the server process to rebuild the index.
- **Sentence-Transformers Dependency Size**: The `sentence-transformers` library and PyTorch runtime require significant disk space and memory during initial installation and execution.

---

## 19. Security Notes

- **Password Hashing**: Passwords are hashed using `bcrypt` with unique salts before being stored in the database. Plaintext passwords are never logged or stored.
- **JWT Expiration & Verification**: Access tokens are signed using `HS256` with a secret key and expire after 60 minutes. Signature validity and expiration are checked on every protected endpoint call.
- **Role-Based Endpoint Protection**: API routes use FastAPI dependency injection (`require_role("agent")`) to enforce server-side role authorization. Route logic verifies that employees can only access their own tickets.
- **Log Sanitization**: A custom `SensitiveDataFilter` is registered across all uvicorn and application loggers to scrub sensitive parameters (such as `token=...`) from application log outputs.
- **Secrets Isolation**: All sensitive credentials (database passwords, JWT secrets, LLM API keys) are loaded strictly from environment variables and excluded from version control via `.gitignore`.
