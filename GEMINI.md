# GEMINI.md: ToTheMoon Project Context

This document provides the essential context for the ToTheMoon project, designed to guide AI agents in understanding and contributing to the codebase.

## 1. Project Overview

**Purpose:** `ToTheMoon` is a sophisticated analysis system designed to identify arbitrage opportunities on the Solana blockchain. It automatically discovers new tokens, analyzes their market data, and applies a scoring algorithm to rank their potential. The ultimate goal is to provide a filtered, prioritized list of tokens to an automated arbitrage bot, thereby optimizing its efficiency and reducing network fee expenditures.

**Architecture:** The system is composed of three main parts:
1.  **Backend Service:** A data processing pipeline that:
    *   Ingests real-time data on new tokens from a WebSocket (`wss://pumpportal.fun/data-api/real-time`).
    *   Enriches token data with market metrics. It uses a hybrid approach:
        *   **Birdeye API:** Provides primary aggregated metrics (liquidity, volume, holders) for scoring.
        *   **DexScreener & Jupiter APIs:** Used together to get detailed per-pool data for validation and health checks.
    *   Manages the lifecycle of each token (Initial, Active, Archived) based on its activity.
    *   Calculates a "Hybrid Momentum" score using a modular, extensible formula.
2.  **Database:** Stores token data, liquidity pool information, and historical metrics required for scoring calculations.
3.  **Frontend UI:** A web-based dashboard that displays lists of tokens by status, their scores, and key metrics with sparkline visualizations for dynamic data. It also includes a detailed view for individual tokens and an admin panel for configuring scoring parameters without code changes.

**Key Document:** For a complete understanding of the business logic, data models, and scoring formulas, refer to the functional specification: [doc/functional_task.md](./doc/functional_task.md).

## 2. Building and Running

*Note: The project currently lacks build scripts and dependency files. The following commands are placeholders based on a presumed Python/FastAPI backend and a TypeScript/React frontend. These should be updated once the project is initialized.*

### Backend (Python/FastAPI)

```bash
# TODO: Initialize a Python environment and create requirements.txt

# Install dependencies
pip install -r requirements.txt

# Run the development server
# (Assumes the main FastAPI app is in `backend/main.py`)
uvicorn backend.main:app --reload
```

### Frontend (TypeScript/React)

```bash
# TODO: Initialize a React project (e.g., with Vite) and create package.json

# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

### Testing

```bash
# TODO: Configure testing frameworks (e.g., pytest for backend, vitest for frontend)

# Run backend tests
# pytest backend/tests/

# Run frontend tests
# cd frontend && npm test
```

## 3. Development Conventions

*   **Modularity:** The scoring system is designed to be modular. New scoring algorithms should be implemented as separate, interchangeable modules as described in the functional specification.
*   **Configuration:** Do not hardcode parameters like scoring weights, API endpoints, or activity thresholds. These should be managed via environment variables or the admin panel.
*   **Data Models:** Adhere to the database schemas outlined in `doc/functional_task.md` when creating or modifying data structures.
*   **Code Style:**
    *   **Python:** Follow PEP 8. Use `black` for formatting and `ruff` for linting.
    *   **TypeScript:** Follow standard TypeScript/React conventions. Use `prettier` for formatting and `eslint` for linting.
*   **Testing:** All new business logic (e.g., a new scoring component) must be accompanied by unit tests.
