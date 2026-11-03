# Inventory & Order Management API

A REST API for managing products, stock levels, and customer orders. Order placement is fully transactional: stock is updated atomically and the whole operation rolls back on failure, so inventory never goes out of sync and items are never oversold, even under concurrent requests.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white)
![Tests](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [How Order Placement Works](#how-order-placement-works)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [API Overview](#api-overview)
- [SQL Reports](#sql-reports)
- [Running Tests](#running-tests)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Author](#author)

---

## Features

- **Products**: Create, read, update, and delete products.
- **Stock Management**: Track and adjust stock levels per product.
- **Orders**: Place and retrieve orders made up of one or more line items.
- **Atomic Order Placement**: Stock deduction and order creation happen in a single database transaction, with automatic rollback on any failure.
- **Overselling Protection**: Safe under concurrent orders, so two simultaneous requests can never claim the same last unit.
- **Request Validation**: Strict input validation with Pydantic models and clear error responses.
- **SQL Reports**: Low-stock and sales reports backed by SQL queries.
- **Schema Migrations**: Versioned database changes with Alembic.
- **Interactive API Docs**: Auto-generated Swagger UI via FastAPI.
- **Tested**: pytest suite that includes concurrent order scenarios.

## Tech Stack

| Layer        | Technologies                         |
| ------------ | ------------------------------------ |
| Framework    | Python, FastAPI                      |
| Database     | PostgreSQL                           |
| ORM          | SQLAlchemy                           |
| Migrations   | Alembic                              |
| Validation   | Pydantic                             |
| Testing      | pytest                               |

## How Order Placement Works

Placing an order runs inside a single database transaction:

1. Validate the request payload with Pydantic.
2. Lock the rows of the products being ordered so concurrent orders cannot read stale stock.
3. Check that every line item has enough stock.
4. Deduct stock and create the order and its items.
5. Commit. If any step fails (for example insufficient stock), the transaction rolls back and nothing is changed.

> Update step 2 to match your implementation (for example `SELECT ... FOR UPDATE`, an atomic conditional `UPDATE`, or an isolation level setting).

## Project Structure

> Adjust this to match your repository layout.

```
inventory-api/
├── app/
│   ├── main.py            # FastAPI entry point
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── routers/           # Products, stock, orders, reports
│   ├── services/          # Business logic (order placement)
│   ├── core/              # Config and settings
│   └── db/                # Session and base setup
├── alembic/               # Database migrations
├── sql/                   # Report queries
├── tests/                 # pytest test suite
├── alembic.ini
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 13+

### 1. Clone the repository

```bash
git clone https://github.com/pvnm4/inventory-order-api.git
cd inventory-order-api
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up the database

```sql
CREATE DATABASE inventory;
```

Copy the environment template and fill in your values:

```bash
cp .env.example .env
```

### 4. Run migrations and start the server

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/inventory
```

## API Documentation

With the server running, interactive docs are available at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Overview

> Endpoint paths are illustrative. Update them to match your routes.

### Products

| Method | Endpoint              | Description            |
| ------ | --------------------- | ---------------------- |
| GET    | `/products`           | List products          |
| POST   | `/products`           | Create a product       |
| GET    | `/products/{id}`      | Get product details    |
| PUT    | `/products/{id}`      | Update a product       |
| DELETE | `/products/{id}`      | Delete a product       |

### Stock

| Method | Endpoint                      | Description                    |
| ------ | ----------------------------- | ------------------------------ |
| GET    | `/products/{id}/stock`        | Get current stock level        |
| PATCH  | `/products/{id}/stock`        | Adjust stock (restock, correct)|

### Orders

| Method | Endpoint           | Description                                   |
| ------ | ------------------ | --------------------------------------------- |
| POST   | `/orders`          | Place an order (atomic stock update)          |
| GET    | `/orders`          | List orders                                   |
| GET    | `/orders/{id}`     | Get order details                             |

**Example: placing an order**

```http
POST /orders
Content-Type: application/json

{
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 4, "quantity": 1 }
  ]
}
```

If any item has insufficient stock, the request fails and no stock is changed:

```json
{
  "detail": "Insufficient stock for product 4"
}
```

### Reports

| Method | Endpoint                 | Description                          |
| ------ | ------------------------ | ------------------------------------ |
| GET    | `/reports/low-stock`     | Products at or below a stock threshold |
| GET    | `/reports/sales`         | Sales summary over a date range      |

## SQL Reports

Reports are powered by SQL queries against the order and product tables.

- **Low stock**: lists products whose stock is at or below a configurable threshold so they can be restocked in time.
- **Sales**: aggregates order data (for example revenue and units sold per product) over a given period.

The queries live in `sql/` (or in the report service). Update this section with the exact location and parameters.

## Running Tests

```bash
pytest
```

With verbose output or coverage:

```bash
pytest -v
pytest --cov=app
```

The suite includes concurrency tests that fire simultaneous orders at the same product to verify stock never goes negative and failed orders leave inventory untouched.

## Roadmap

- [ ] JWT authentication and role-based access
- [ ] Order status workflow (pending, paid, shipped, cancelled)
- [ ] Pagination and filtering on list endpoints
- [ ] Docker and docker-compose setup
- [ ] CI pipeline with GitHub Actions

## Author

**Pavan Mhaisne**

- GitHub: [@pvnm4](https://github.com/pvnm4)
- LinkedIn: [pvnm4](https://linkedin.com/in/pvnm4)
