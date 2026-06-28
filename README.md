# ServicesMarketplace

Backend for a professional services marketplace (Upwork-style) with escrow payments, real-time messaging, and fund release controlled by Stripe webhooks.

A **client** publishes a project (`Job`), **professionals** apply (`Application`), the client accepts a proposal and a **contract** (`Contract`) is generated. The client's money stays held in escrow until the client approves the delivery, at which point it's released to the professional. Clients and professionals can negotiate project details through a real-time chat on the platform via WebSockets.

---

## Table of contents

- [Tech stack](#tech-stack)
- [Project architecture](#project-architecture)
- [Data model](#data-model)
- [End-to-end business flow](#end-to-end-business-flow)
- [Security and authorization](#security-and-authorization)
- [Payments and escrow with Stripe](#payments-and-escrow-with-stripe)
- [Stripe webhooks](#stripe-webhooks)
- [Real-time messaging (WebSockets)](#real-time-messaging-websockets)
- [API endpoints](#api-endpoints)
- [Environment variables](#environment-variables)
- [Running the project](#running-the-project)
- [Testing](#testing)
- [Known limitations and roadmap](#known-limitations-and-roadmap)

---

## Tech stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 (`Mapped`/`mapped_column` style) |
| Migrations | Alembic |
| Database | PostgreSQL 16 |
| Authentication | JWT (`python-jose`) + `passlib` (bcrypt) |
| Payments | Stripe (PaymentIntents, Transfers, Refunds, Connect Express, Webhooks) |
| Real-time | Native FastAPI WebSockets |
| Testing | Pytest + `TestClient` + `unittest.mock` |
| Containers | Docker + Docker Compose |

---

## Project architecture

The project follows a layered architecture:

```
routers/      → Defines HTTP/WS endpoints. Validates input, translates service results
                 into HTTP status codes. Contains no business logic.
services/     → Contains all business logic. Receives a DB session and returns
                 objects, status dicts ("NOT_FOUND", "FORBIDDEN", etc.), or data
                 ready to be serialized.
models/       → SQLAlchemy tables (ORM).
schemas/      → Pydantic models for request/response.
dependencies/ → Reusable FastAPI dependencies: authentication (auth.py) and
                 role-based authorization (roles.py).
core/         → Configuration (settings.py) and security utilities (security.py).
database/     → SQLAlchemy engine and session.
ws/           → ConnectionManager: tracks active WebSocket connections per conversation.
alembic/      → Database migrations.
tests/        → Pytest suite (fixtures in conftest.py).
```

Service response pattern: instead of raising HTTP exceptions directly, services return status strings (`"NOT_FOUND"`, `"FORBIDDEN"`, `"INVALID_STATUS"`, `"STRIPE_ERROR"`, etc.) which the router translates into the appropriate HTTP status code. This keeps business logic decoupled from FastAPI and makes it easier to test in isolation.

---

## Data model

### Core entities

| Model | Description |
|---|---|
| `User` | Platform user. Role: `ADMIN`, `CLIENT`, or `PROFESSIONAL`. The first user ever registered in the system automatically becomes `ADMIN`. |
| `Profile` | Extended user profile (description, social media, experience, abilities). Created empty automatically on registration. |
| `Abilitie` | Catalog of skills/abilities. Only an `ADMIN` can create them; users select them from their profile. |
| `Job` | Project published by a `CLIENT`. |
| `Application` | Proposal from a `PROFESSIONAL` to a `Job`. Status: `PENDING`, `ACEPTED`, `REJECTED`. |
| `Contract` | Formal agreement between buyer and seller, generated when an `Application` is accepted. This is where the entire escrow state lives. |
| `Conversation` | Messaging channel between two users. Only created when a `Contract` is created. |
| `Notification` | Individual message inside a `Conversation`. |

### Association tables (many-to-many)

- `abilities_profile`: relates `Profile` ↔ `Abilitie`.
- `abilities_job`: relates `Job` ↔ `Abilitie` (skills required for the project).

### `Contract` detail — the heart of the escrow system

```
contract_id          UUID (PK)
job_id               FK → job.job_id
seller_id            FK → users.user_id   (professional who receives the payment)
buyer_id             FK → users.user_id   (client who pays)
status               PENDING_PAYMENT | GUARANTEED | COMPLETED | REFUNDED | FAILED | DISPUTED
amount               Decimal
detail               text (description of the work to be delivered)
payment_intent_id    Stripe ID (PaymentIntent) — set when payment is initiated
charge_id            Stripe ID (Charge) — set when the webhook confirms the charge
transfer_id          Stripe ID (Transfer) — fund release to the professional
refund_id            Stripe ID (Refund) — if the contract is refunded
created_at / updated_at
```

Each of the four Stripe IDs (`payment_intent_id`, `charge_id`, `transfer_id`, `refund_id`) is stored separately to keep full traceability of which stage of the money's lifecycle the contract is in, without having to query the Stripe API to reconstruct the history.

### `Contract` state machine

```
PENDING_PAYMENT  → (client pays, PaymentIntent succeeded) →  GUARANTEED
GUARANTEED       → (client approves delivery, Transfer created) →  COMPLETED
GUARANTEED       → (client requests a refund, Stripe confirms) →  REFUNDED
PENDING_PAYMENT  → (payment fails in Stripe) →  FAILED
GUARANTEED       → (a dispute is opened in Stripe) →  DISPUTED
```

All real state transitions (except the initial request) happen **inside the webhook handlers**, never directly from the endpoint the client calls. This is intentional: the HTTP endpoint only *requests* the operation from Stripe; the contract's status only changes once Stripe confirms the money actually moved.

---

## End-to-end business flow

1. **Registration** — `POST /auth/register`. If the role is `PROFESSIONAL`, a Stripe Connect (Express) account is automatically created and an onboarding link is generated so the professional can receive transfers.
2. **Project posting** — `POST /jobs`, `CLIENT` only.
3. **Application** — `POST /jobs/{job_id}/apply`, `PROFESSIONAL` only. A professional cannot apply twice to the same project.
4. **Proposal acceptance** — `POST /application/{application_id}/accept`, only the `CLIENT` who owns the project. In a single atomic transaction, this action:
   - Creates the `Contract` (status `PENDING_PAYMENT`).
   - Marks the accepted `Application` as `ACEPTED`.
   - Deactivates the `Job` (`is_active = False`) so it stops receiving new applications.
   - Creates the `Conversation` between client and professional (if it didn't already exist).
   - Sends an initial message over WebSocket.
5. **Payment / Escrow** — `POST /contracts/{contract_id}/pay`, contract `buyer` only. Creates a `PaymentIntent` in Stripe and returns the `client_secret` so the frontend can confirm the charge with Stripe.js/Elements.
6. **Payment confirmation (webhook)** — Stripe notifies `payment_intent.succeeded`. The contract moves to `GUARANTEED` and the `charge_id` is stored.
7. **Negotiation** — client and professional chat over WebSocket while the work is carried out.
8. **Approval and fund release** — `POST /contracts/{contract_id}/completed`, `buyer` only. Creates a `Transfer` in Stripe to the professional's connected account.
9. **Transfer confirmation (webhook)** — Stripe notifies `transfer.created`. The contract moves to `COMPLETED`.
10. **(Alternative) Refund** — `POST /contracts/{contract_id}/refund`, `buyer` only, only if the contract is `GUARANTEED`. Stripe processes the `Refund`; the `charge.refunded` webhook marks the contract as `REFUNDED`.
11. **(Alternative) Dispute** — if the buyer opens a dispute directly on Stripe, the `charge.dispute.created` webhook marks the contract as `DISPUTED`.

---

## Security and authorization

### Authentication

- JWT signed with `HS256`, generated in `core/security.py` (`return_token`) and validated in `dependencies/auth.py`.
- The token includes the `user_id` in the `sub` claim and expires according to `TOKEN_DURATION` (minutes).
- `get_user` (HTTP) and `get_user_websocket` (WS) decode the token, load the user from the database, and verify they're active (`is_active`).

### Role-based authorization

`dependencies/roles.py` exposes dependencies ready to inject into any endpoint:

| Dependency | Allows |
|---|---|
| `get_admin` | `ADMIN` only |
| `get_client` | `CLIENT` only |
| `get_professional` | `PROFESSIONAL` only |
| `get_admin_client` | `ADMIN` or `CLIENT` |

### Resource-ownership authorization

Having the right role **is not enough** — every sensitive operation additionally validates that the authenticated user actually owns the specific resource they're trying to act on:

- **Jobs**: only the owning `client_id` can edit or deactivate it (an `ADMIN` can do so on any job, acting as a platform moderator).
- **Contracts / money**: paying, refunding, or releasing funds requires `contract.buyer_id == current_user.user_id`. No other registered client, even with the right role, can operate on someone else's contract.
- **Conversations**: the WebSocket validates with `verify_conversation` that a real `Conversation` exists between the authenticated user and the other participant **before** accepting the connection. Conversations aren't freely created between any pair of users — they only come into existence as a consequence of accepting an `Application` and generating a `Contract`. This prevents a user from opening a messaging channel with someone they have no business relationship with.

### Stripe webhooks

The `POST /webhook/stripe` endpoint validates the cryptographic signature of the payload (`stripe-signature` header) against `stripe.Webhook.construct_event(...)` using `STRIPE_WEBHOOK_SECRET`. If the signature is invalid, the request is rejected with `400` before processing anything. This prevents a third party from forging a "payment succeeded" notification and forcing the release of funds without the actual charge having occurred on Stripe.

---

## Payments and escrow with Stripe

The project uses **Stripe Connect (Express accounts)** under the *separate charges and transfers* model:

1. The `PaymentIntent` money is charged **to the platform's account** (not directly to the professional).
2. When the client approves the delivery, a `Transfer` is executed from the platform's balance to the professional's connected account (`seller.stripe_connect_id`), using the original `charge_id` as a reference (`source_transaction`).
3. This gives the platform full control over when the money is released — which is precisely the escrow mechanism.

### Relevant functions (`services/contract_services.py`)

| Function | Action on Stripe | Who can call it |
|---|---|---|
| `guaranteed_contract` | `stripe.PaymentIntent.create(...)` | Contract `buyer`, contract in `PENDING_PAYMENT` |
| `reject_contrat` | `stripe.Refund.create(...)` | Contract `buyer`, contract in `GUARANTEED` |
| `contract_fullfiled` | `stripe.Transfer.create(...)` | Contract `buyer`, contract in `GUARANTEED`, active seller |

Each of these functions explicitly distinguishes between Stripe errors (`stripe.StripeError`) and unexpected internal errors, returning a different status (`"STRIPE_ERROR"` vs `"INTERNAL_SERVER_ERROR"`) so the router can respond with the appropriate HTTP code in each case.

---

## Stripe webhooks

`routers/webhooks.py` listens on the `POST /webhook/stripe` endpoint and reacts to the following events:

| Stripe event | Action | New contract status |
|---|---|---|
| `payment_intent.succeeded` | `guarantee_contract` | `PENDING_PAYMENT` → `GUARANTEED` |
| `transfer.created` | `contract_paid` | `GUARANTEED` → `COMPLETED` |
| `payment_intent.payment_failed` | `contract_failed` | `PENDING_PAYMENT` → `FAILED` |
| `charge.refunded` | `contract_refund` | `GUARANTEED` → `REFUNDED` |
| `charge.dispute.created` | `contract_disputed` | `GUARANTEED` → `DISPUTED` |

Each handler:

1. Verifies the contract exists and is in the expected status before transitioning (this prevents double-processing the same event if Stripe retries the webhook delivery).
2. Updates the status and the corresponding IDs (`charge_id`, `refund_id`, etc.).
3. Creates a `Notification` informing of the change in the conversation associated with the contract.
4. Queues the delivery of that notification over WebSocket as a background task, so as not to block the response to Stripe.

Processing happens in the background (`BackgroundTasks`) so the endpoint responds to Stripe immediately — Stripe expects a fast response and automatically retries if it doesn't receive one in time.

---

## Real-time messaging (WebSockets)

### Connection

```
WS /ws/{user_id}?token={jwt}
```

- `token` is validated with the same JWT logic used by HTTP routes (`get_user_websocket`).
- `user_id` in the URL is the **other participant** in the conversation (not the authenticated user).
- Before accepting the connection, `verify_conversation` checks that a real `Conversation` exists between `current_user` and `user_id`. If it doesn't, the connection is rejected (close code `1008`) without sending any data.
- On connect, pending (unread) notifications for that conversation are delivered and marked as read.
- While the connection is open, every received message is persisted as a `Notification` row and broadcast in real time to every client connected to that same conversation through the `ConnectionManager`.

### `ConnectionManager` (`ws/manager.py`)

Keeps an in-memory dictionary `conversation_id → [WebSocket]` of active connections. When a client disconnects, it's removed from the list; if a conversation ends up with no active connections, its entry is removed from the dictionary entirely.

> **Scalability note:** this `ConnectionManager` keeps connection state in the process's memory. It works correctly with a single server instance. If the project is scaled horizontally (multiple API replicas), a shared pub/sub mechanism (e.g. Redis) would be needed to synchronize connections across instances.

---

## API endpoints

### Auth (`/auth`)

| Method | Route | Description | Access |
|---|---|---|---|
| POST | `/auth/register` | Registers a user (`CLIENT` or `PROFESSIONAL`). The first user in the system automatically becomes `ADMIN`. | Public |
| POST | `/auth/login` | Authenticates and returns a JWT. | Public |

### Users (`/users`)

| Method | Route | Description | Access |
|---|---|---|---|
| GET | `/users/me` | Authenticated user's profile. | Authenticated |
| PATCH | `/users/me` | Updates the own profile (description, social media, abilities, experience). | Authenticated |
| GET | `/users/clients` | Paginated list of clients (filters: username, description). | Authenticated |
| GET | `/users/professionals` | Paginated list of professionals (filters: username, description, abilities). | Authenticated |
| GET | `/users/{user_id}` | Public profile of a user. | Authenticated |
| DELETE | `/users/{user_id}/deactivate` | Deactivates a user (and their active jobs, if a client). Cannot deactivate another `ADMIN`. | Admin |

### Abilities (`/abilities`)

| Method | Route | Description | Access |
|---|---|---|---|
| POST | `/abilities` | Creates a new ability in the catalog. | Admin |
| GET | `/abilities` | Lists all available abilities. | Authenticated |

### Jobs (`/jobs`)

| Method | Route | Description | Access |
|---|---|---|---|
| POST | `/jobs` | Publishes a new project. | Client |
| GET | `/jobs` | Paginated list of active projects (filters: text search, abilities, budget). | Authenticated |
| GET | `/jobs/my-jobs` | Projects published by the authenticated client. | Client |
| GET | `/jobs/{job_id}` | Project detail. | Authenticated |
| POST | `/jobs/{job_id}/apply` | Submits a proposal to a project. | Professional |
| PATCH | `/jobs/{job_id}/update` | Edits a project owned by the user. | Client (owner) |
| DELETE | `/jobs/{job_id}/delete` | Deactivates a project (soft delete). | Client (owner) or Admin |

### Applications (`/application`)

| Method | Route | Description | Access |
|---|---|---|---|
| GET | `/application/my-applications` | Applications submitted by the authenticated professional. | Professional |
| GET | `/application/{job_id}` | Applications received for an owned project. | Client (job owner) |
| POST | `/application/{application_id}/accept` | Accepts a proposal: creates the contract, the conversation, deactivates the job, and marks the application as accepted. | Client (job owner) |

### Contracts (`/contracts`)

| Method | Route | Description | Access |
|---|---|---|---|
| GET | `/contracts` | Contracts the authenticated user participates in (as buyer or seller). | Authenticated |
| POST | `/contracts/{contract_id}/pay` | Initiates the escrow charge (`PaymentIntent`). | Contract buyer |
| POST | `/contracts/{contract_id}/refund` | Requests a refund of the escrowed amount. | Contract buyer |
| POST | `/contracts/{contract_id}/completed` | Approves the delivery and releases the payment to the professional. | Contract buyer |

### Webhooks (`/webhook`)

| Method | Route | Description | Access |
|---|---|---|---|
| POST | `/webhook/stripe` | Receives Stripe events and updates contract status. | Stripe (signature-validated) |

### WebSockets (`/ws`)

| Route | Description | Access |
|---|---|---|
| `WS /ws/{user_id}` | Real-time messaging channel with another participant of an existing conversation. | Authenticated via JWT query param |

---

## Environment variables

Create a `.env` file at the project root (you can base it on `.env.example`):

```dotenv
# Database
DATABASE_URL=postgresql+psycopg2://user:password@db:5432/db_name
TESTS_DATABASE_URL=postgresql+psycopg2://user:password@db_test:5432/tests_db_name
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_NAME=db_name
TESTS_POSTGRES_NAME=tests_db_name

# Authentication
SECRET_KEY=your_super_secret_key
ALGORITHM=HS256
TOKEN_DURATION=60

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

> **Important:** the hostname used in `DATABASE_URL`/`TESTS_DATABASE_URL` (`db`, `db_test`) must exactly match the service name defined in `docker-compose.yml`, since Docker Compose resolves those names within its internal network. If you run the API outside of Docker, you'll need to swap them for `localhost` and the corresponding published port.

---

## Running the project

### With Docker (recommended)

```bash
# 1. Set up your .env file (see previous section)
cp .env.example .env

# 2. Bring up all services (API + Postgres + test Postgres)
docker compose up --build

# The API is available at http://localhost:8000
# Interactive docs (Swagger): http://localhost:8000/docs
```

The API container automatically runs `alembic upgrade head` before starting `uvicorn`, so migrations are applied on every startup.

> Note: the first user who registers in the system (`POST /auth/register`) automatically becomes `ADMIN`, regardless of the role they request. It's recommended to register your admin user immediately after the first deployment, before exposing the API publicly.

### Manually (without Docker)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

# Make sure Postgres is running locally and adjust
# DATABASE_URL in your .env to point to localhost instead of "db"

alembic upgrade head
uvicorn main:app --reload
```

---

## Testing

```bash
pytest
```

The suite uses a separate Postgres database (`TESTS_DATABASE_URL`) and a transaction-plus-rollback pattern per test: each test runs inside its own SQLAlchemy transaction, which is rolled back at the end, so there's no need to manually clean up data between tests.

### Coverage by module

| File | Covers |
|---|---|
| `test_auth.py` | Registration (client and professional with mocked Stripe), duplicate email, valid/invalid login. |
| `test_users.py` | Own profile, client/professional listings, user deactivation. |
| `test_abilities.py` | Ability creation (admin only), listing, rejection by incorrect role. |
| `test_job.py` | Posting, editing, deactivating, and applying to projects — including **negative authorization**: a client cannot edit/delete another client's project, a professional cannot edit projects, a professional cannot apply twice to the same project. |
| `test_webhooks.py` | Simulation of Stripe payloads (`payment_intent.succeeded`, `payment_intent.payment_failed`, etc.) without making real calls to Stripe, by mocking the database session and the background tasks. |

### Testing principles applied

- **No real charges:** every call to the Stripe API is intercepted with `unittest.mock.patch`. The webhook tests exercise the functions in `services/webhooks_services.py` directly, simulating the payload Stripe would have sent, with no need to expose a public endpoint to the internet or to generate real events from the Stripe dashboard.
- **Authorization as a first-class citizen:** for every resource protected by ownership (projects, contracts, conversations), there's at least one "happy path" test (the owner can act on it) and one negative-authorization test (an unrelated user gets the expected error code). This was an explicit requirement of the project: never assume protection works just because the code "looks right" — prove it with an automated test.
- **Mocks with `spec`:** mocks for objects like `BackgroundTasks` are created with `MagicMock(spec=BackgroundTasks)`, so a typo or a call to a non-existent method breaks the test loudly instead of silently passing.

> **Suite scope:** the API tests all run on the same database session per test request, within the same transaction. This correctly validates business logic and authorization, but does not reproduce real concurrency conditions (e.g. two simultaneous requests competing for the same resource). It should not be interpreted as a guarantee of behavior under concurrent load.

---