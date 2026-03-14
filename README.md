# MemoryVest

A Modern, Beginner-Friendly Investing Companion

MemoryVest is a full-stack investing companion that uses EverMemOS as its long-term memory layer to securely track your investment profile, portfolio holdings, and future interests. It features a modern React dashboard and a conversational AI assistant that automatically updates your portfolio and settings as you chat.

## Features

- **Conversational Memory**: Uses an LLM agent with EverMemOS to dynamically learn your preferences over time.
- **RESTful Backend API**: Built on a modular FastAPI architecture (`/api/market`, `/api/profile`, `/api/chat`, `/api/portfolio`) using SQLite for robust local data persistence.
- **React Web Dashboard**: A sleek, custom Vanilla CSS frontend (Vite) featuring a real-time Portfolio Dashboard, CSV drag-and-drop import, and a responsive AI Chat UI.
- **Live Market Data**: Integrates with `yfinance` to actively hydrate your web UI with real-time stock prices and return calculations.
- **Automated Reporting**: Generates a beginner-friendly daily stock report using LLMs (OpenAI or OpenRouter) and can send formatted emails.

---

## Getting Started

MemoryVest is composed of two layers: a FastAPI backend and a Vite+React frontend.

### 1. Initialize the Database
Run this once from the project root to set up your local SQLite database schemas within the `app/infra` layer.
```bash
uv run memoryvest init
```

### 2. Start the Backend API Server
In the root directory, spin up the FastAPI backend on port 8000:
```bash
uv run uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Start the Web Dashboard
Open a new terminal, navigate to the `frontend` folder, and start Vite:
```bash
cd frontend
npm install
npm run dev
```

Visit the local URL provided by Vite (usually `http://localhost:5173`) to open the Web Dashboard!

---

## Interactive Chat Mode

The core experience of MemoryVest is designed around a natural language assistant, available directly in the Web Dashboard or via the terminal. You do not need to learn complex commands to update your portfolio or set your preferences.

The AI will parse your natural language sentences, reply to you conversationally (like ChatGPT), and automatically execute REST API calls to update your profile, portfolio, and cash balance under the hood.

### Chat Examples

You can tell the assistant any combination of facts:

*   **Setup your profile**: 
    > "I'm a beginner investor with a low risk tolerance. I'm really interested in AI and gaming stocks. Please keep explanations simple."
*   **Set your email**:
    > "My email address is me@example.com."
*   **Update your portfolio**:
    > "I just bought 15 shares of Apple at $168.50."
    > "I added 2.5 shares of NVDA to my portfolio."
*   **Update Cash**:
    > "I have $3500 sitting in cash ready to invest."
*   **Track Future Intents**:
    > "Can you watch AMD for me? Let me know if it dips below 135."

---

## Legacy CLI Operations

You can still bypass the Web UI and update your settings or run custom reports entirely from the CLI. You must provide a `--user-id` (e.g., `anon`) for every command.

```bash
# List all stored user IDs
uv run memoryvest --list-users

# Start an interactive CLI chat session (updates your profile/portfolio natively)
uv run memoryvest chat --user-id anon

# Generate a Preview of the Daily Email Report
uv run memoryvest report preview --user-id anon

# Send Email Report (requires .env SMTP variables)
uv run memoryvest report send --user-id anon
```

You can append the `--verbose` or `-v` flag to any command to enable trace logging. This is incredibly helpful for seeing exactly what data is being sent to the LLMs and what raw JSON they are returning.
