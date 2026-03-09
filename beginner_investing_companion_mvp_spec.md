# Technical Specification: Beginner-Friendly Investing Companion MVP

## 1. Overview

### 1.1 Product Name
**Working name:** MemoryVest

### 1.2 Product Summary
MemoryVest is a CLI-based investing companion for everyday users. It uses EverMemOS as its long-term memory layer to remember:
- who the user is,
- what the user owns,
- what sectors/themes the user cares about,
- how much investing experience the user has,
- how much cash the user has available,
- what kind of explanations and alerts the user prefers.

Each trading day after the market closes, the system retrieves the user’s relevant memories, gathers stock and sector performance plus material news from the web, generates a beginner-friendly personalized report, and emails the report to the user.

The MVP is not a professional trading tool. It is a consumer-facing memory-powered market brief assistant focused on clarity, personalization, and continuity over time.

---

## 2. Goals and Non-Goals

### 2.1 Goals
- Build a working EverMemOS-powered agent that demonstrates persistent user memory.
- Provide a CLI that supports natural user interaction and structured portfolio updates.
- Generate a personalized daily market brief for beginner investors.
- Use memory to reduce noise and tailor tone, detail, and relevance.
- Email the report automatically after market close.
- Keep the system simple enough to demo reliably during a hackathon.

### 2.2 Non-Goals
- Real-time intraday trading alerts.
- Full brokerage integration.
- Automated trading or order execution.
- Advanced portfolio optimization.
- Options, futures, margin, or professional-grade analytics.
- Registered investment advice or buy/sell recommendations.

---

## 3. Target User

### 3.1 Primary User
Average retail investors who:
- own a small portfolio,
- may follow a few companies or sectors,
- do not want highly technical tools,
- want to understand what happened and why it matters,
- benefit from plain-English explanations.

### 3.2 User Traits Captured in Memory
- investing experience level,
- risk preference,
- holdings and cost basis,
- cash available for investing,
- interests/hobbies tied to sectors,
- preferred explanation style,
- desired report frequency,
- alert sensitivity,
- current watchlist,
- future investing intentions.

---

## 4. User Experience

## 4.1 CLI Experience
The CLI supports both:
1. structured commands, and
2. conversational chat mode.

### Example Structured Commands
```bash
memoryvest init
memoryvest profile show
memoryvest add-position AAPL 10 185.40
memoryvest add-position NVDA 5 121.20
memoryvest add-cash 3000
memoryvest add-interest "AI"
memoryvest add-interest "gaming"
memoryvest set-style beginner
memoryvest set-frequency daily
memoryvest report preview
memoryvest report send
memoryvest memory recent
```

### Example Chat Mode
```text
> I’m a beginner investor.
> I own 10 shares of Apple at 185.40.
> I own 5 shares of Nvidia at 121.20.
> I have about 3000 dollars in cash.
> I care about AI and gaming.
> Keep explanations simple and don’t use too much jargon.
> Email me a daily report after the market closes.
```

### Design Principle
The user should feel like they are talking to a personal assistant, not operating a finance terminal.

---

## 5. MVP Scope

### 5.1 Included in MVP
- CLI onboarding flow
- conversational and structured input parsing
- EverMemOS integration for memory storage and retrieval
- user profile memory persistence
- positions/watchlist/cash persistence
- daily post-close scheduled job
- market data retrieval for tracked stocks and relevant sectors
- news retrieval and summarization
- beginner-friendly report generation
- basic support/resistance level generation
- email delivery
- simple audit/event history

### 5.2 Excluded from MVP
- mobile app or web UI
- real-time push notifications
- portfolio performance charting dashboard
- social sentiment analysis
- tax lot accounting
- advanced technical indicators beyond simple price levels

---

## 6. System Architecture

The system is composed of five main layers:

1. **CLI Layer**
2. **Application Service Layer**
3. **Memory Layer (EverMemOS)**
4. **Market Intelligence Layer**
5. **Delivery Layer**

### 6.1 High-Level Flow
1. User interacts with CLI.
2. CLI sends user input to the intake/orchestration service.
3. Input is normalized and stored in EverMemOS.
4. At scheduled time, the daily report job runs.
5. Job retrieves user context from EverMemOS.
6. Job fetches market prices, sector data, and relevant news.
7. Job generates a personalized report.
8. Job sends the report by email.
9. Job writes report metadata back into memory/event history.

### 6.2 Components

#### A. CLI Layer
Responsibilities:
- accept user input,
- support chat and command mode,
- display memory-aware responses,
- trigger preview/send flows.

#### B. Intake/Orchestration Layer
Responsibilities:
- classify input intent,
- extract structured entities,
- normalize holdings/profile/preferences,
- call EverMemOS APIs,
- coordinate retrieval and generation.

#### C. EverMemOS Memory Layer
Responsibilities:
- store user messages,
- retain long-term context,
- retrieve relevant memory for report generation,
- provide continuity across sessions.

#### D. Market Intelligence Layer
Responsibilities:
- fetch daily stock/sector performance,
- fetch relevant news,
- rank relevance to user profile and holdings,
- compute simple support/resistance ranges.

#### E. Delivery Layer
Responsibilities:
- render email-safe report format,
- send email,
- persist send outcome to event history.

---

## 7. Technology Stack

### 7.1 Core Stack
- **Language:** Python 3.11+
- **CLI framework:** Typer
- **HTTP client:** httpx
- **Task scheduling:** APScheduler or cron-triggered Python entrypoint
- **Email:** SMTP or transactional provider API (e.g. Resend/SendGrid)
- **LLM orchestration:** lightweight wrapper around chosen model provider
- **Configuration:** pydantic-settings / dotenv
- **Logging:** structlog or Python logging
- **Packaging:** uv or poetry

### 7.2 External Systems
- **EverMemOS API server** for memory persistence and retrieval
- **Market data API** for end-of-day prices and sector ETFs
- **News API / web search provider** for headline retrieval and article metadata
- **LLM provider** for summarization and user-facing explanation generation
- **SMTP/email provider** for report delivery

---

## 8. EverMemOS Integration Design

## 8.1 Memory Strategy
The MVP should use EverMemOS for more than raw storage. It should use memory to personalize content selection, explanation depth, and alerting behavior.

### 8.1.1 Memory Categories Used

#### Profile Memory
Use for stable user attributes:
- investor experience level,
- risk preference,
- explanation style,
- jargon tolerance,
- report frequency,
- report length preference,
- email address,
- sector interests,
- hobby-linked themes.

#### Episodic Memory
Use for user interactions and evolving financial context:
- user updates a holding,
- user says they are nervous about a sector,
- user asks to follow a specific company,
- user changes how much detail they want.

#### Foresight
Use for future intent:
- user wants to add money next month,
- user wants to watch a buy zone,
- user wants a reminder if a stock approaches a level,
- user wants to reduce exposure later.

#### Event Log
Use for system actions and deduplication:
- report sent,
- report failed,
- major news already mentioned,
- last generated support/resistance snapshot,
- scheduled run status.

## 8.2 Memory Write Patterns
For each user interaction, the app writes:
1. the raw user message, and
2. a normalized internal state update.

### Example
User says:
> I own 10 shares of Apple at 185.40 and 5 shares of Nvidia at 121.20. I also have 3000 cash.

The system should:
- store the original natural-language message,
- update normalized portfolio state in application storage,
- write a corresponding memory note/event that this portfolio context was updated.

## 8.3 Retrieval Patterns
The daily report job should not rely on one broad memory search. It should issue several focused retrieval tasks:
- What holdings does the user currently own?
- What sectors or themes matter to the user?
- What explanation style does the user prefer?
- What future intentions should be checked?
- What major events have already been mentioned recently?

## 8.4 Recommended Retrieval Rules
- Use `hybrid` retrieval by default for daily report context.
- Use `keyword` retrieval for exact recall tasks when the query is highly specific.
- Use `agentic` retrieval only for optional advanced debugging or future v2 workflows due to added latency/cost.
- Do not depend on searching `profile` via the search interface; maintain a normalized user profile store in the application and treat EverMemOS search as support for episodic, foresight, and event-log recall.

## 8.5 Why a Local Normalized Store Is Still Needed
EverMemOS is the long-term memory engine, but the MVP should also maintain a deterministic application state store for canonical facts such as:
- current positions,
- current cash,
- email address,
- current delivery settings,
- active watchlist.

This is needed because financial state should be deterministic and easy to render even when conversational memory retrieval is partial.

---

## 9. Data Model

## 9.1 Canonical Application Models

### UserProfile
```json
{
  "user_id": "user_001",
  "email": "user@example.com",
  "experience_level": "beginner",
  "risk_tolerance": "moderate",
  "explanation_style": "plain_english",
  "jargon_tolerance": "low",
  "report_frequency": "daily",
  "report_length": "short",
  "timezone": "America/Los_Angeles",
  "interests": ["AI", "gaming"],
  "sector_preferences": ["technology", "semiconductors"],
  "alert_sensitivity": "important_only"
}
```

### Position
```json
{
  "user_id": "user_001",
  "ticker": "AAPL",
  "shares": 10,
  "avg_cost": 185.40,
  "opened_at": "2026-03-01T20:00:00Z",
  "status": "open"
}
```

### CashBalance
```json
{
  "user_id": "user_001",
  "available_cash": 3000.00,
  "currency": "USD",
  "updated_at": "2026-03-08T20:00:00Z"
}
```

### WatchIntent
```json
{
  "user_id": "user_001",
  "ticker": "AMD",
  "type": "price_watch",
  "note": "Interested on pullback",
  "target_zone_low": 135,
  "target_zone_high": 140,
  "status": "active"
}
```

### ReportHistory
```json
{
  "report_id": "rpt_2026_03_08_user_001",
  "user_id": "user_001",
  "generated_at": "2026-03-08T23:10:00Z",
  "delivery_status": "sent",
  "headline_topics": ["semiconductors", "AI infrastructure"],
  "mentioned_tickers": ["NVDA", "AAPL"],
  "email_provider_id": "msg_123"
}
```

## 9.2 EverMemOS Message Envelope
All user-originated interactions written to EverMemOS should include:
- `message_id`
- `create_time`
- `sender`
- `content`
- `user_id`
- optional `group_id`
- optional metadata such as scene/source

Example write payload:
```json
{
  "message_id": "msg_20260308_001",
  "create_time": "2026-03-08T20:00:00+00:00",
  "sender": "user_001",
  "content": "I own 10 shares of Apple at 185.40 and I prefer simple explanations.",
  "user_id": "user_001",
  "group_id": "memoryvest_user_001"
}
```

---

## 10. Services and Modules

## 10.1 CLI Module
Responsibilities:
- command parsing,
- interactive chat loop,
- preview report display,
- memory inspection commands.

Commands:
- `init`
- `chat`
- `profile show`
- `profile update`
- `add-position`
- `update-position`
- `remove-position`
- `add-cash`
- `add-interest`
- `add-watch`
- `report preview`
- `report send`
- `memory recent`
- `why-this-report`

## 10.2 Memory Service
Responsibilities:
- write raw messages to EverMemOS,
- search relevant memories,
- fetch/report memory-backed context,
- write event-log records.

Primary methods:
- `store_user_message(...)`
- `search_episodic_context(...)`
- `search_foresight_context(...)`
- `store_report_event(...)`
- `store_delivery_event(...)`

## 10.3 Profile/Portfolio Service
Responsibilities:
- deterministic persistence of canonical state,
- sync between parsed conversation state and local store,
- validation of tickers/shares/cost basis.

## 10.4 Market Data Service
Responsibilities:
- fetch latest end-of-day prices,
- fetch daily percentage changes,
- fetch benchmark and sector ETF context,
- provide historical candles for support/resistance calculations.

Suggested baseline sector proxies:
- Technology: XLK
- Semiconductors: SOXX or SMH
- Energy: XLE
- Financials: XLF
- Healthcare: XLV
- Consumer Discretionary: XLY

## 10.5 News Service
Responsibilities:
- fetch relevant articles for owned tickers,
- fetch sector/theme news for user interests,
- deduplicate similar stories,
- rank by user relevance,
- produce article snippets for report generation.

## 10.6 Analysis Service
Responsibilities:
- derive portfolio-level summary,
- rank key movers,
- compute support/resistance,
- convert market/news data into beginner-friendly insights.

## 10.7 Report Generation Service
Responsibilities:
- construct report sections,
- adapt tone/length to user profile,
- produce email HTML + plain text,
- produce CLI preview.

## 10.8 Delivery Service
Responsibilities:
- send email,
- handle retries,
- log success/failure,
- write send outcome to event history.

## 10.9 Scheduler Service
Responsibilities:
- run post-close jobs,
- support per-user timezone schedules in future,
- enforce idempotency for same-day reports.

---

## 11. Report Generation Specification

## 11.1 Daily Report Objectives
Each report must answer five beginner-friendly questions:
1. What happened today?
2. What mattered to my holdings?
3. What mattered to my interests/watchlist?
4. Why does it matter in plain English?
5. What simple levels or themes should I watch next?

## 11.2 Report Structure

### Section A: 30-Second Summary
Example:
- Your tracked portfolio finished modestly higher today.
- Semiconductor stocks outperformed.
- Apple was relatively stable while Nvidia gained on AI-related optimism.
- No urgent portfolio risk signal stood out today.

### Section B: Portfolio Snapshot
For each holding:
- ticker,
- day change,
- notable reason if available,
- one-sentence interpretation.

### Section C: Sectors and Themes You Care About
- AI
- gaming
- clean energy
- semiconductors

Only include themes remembered as relevant to the user.

### Section D: News That Actually Matters To You
Rank news by:
1. owned tickers,
2. active watchlist,
3. user interests,
4. broad market context.

### Section E: Simple Technical Watch Levels
For each major tracked ticker:
- approximate support,
- approximate resistance,
- short explanation of what those levels mean.

### Section F: What To Watch Next
Examples:
- Watch whether Nvidia holds above recent support.
- Watch whether Apple gets additional product or services-related follow-through.
- Watch whether semiconductor strength broadens beyond one stock.

### Section G: Reminder / Disclaimer
- informational only,
- not financial advice,
- support/resistance levels are approximate.

## 11.3 Tone Rules
- plain English first,
- avoid dense financial jargon,
- avoid panic language,
- avoid imperative buy/sell instructions,
- prefer explanations like “this may matter because…”

---

## 12. Support and Resistance Calculation

## 12.1 MVP Approach
Use a simple heuristic rather than advanced technical analysis.

Inputs:
- last 30 to 90 trading days of price data,
- recent highs/lows,
- local swing points,
- optionally moving average context.

Output:
- `support_zone`
- `resistance_zone`
- confidence label: low / medium / high

## 12.2 Heuristic Example
- support = recent local low cluster or 20-day low area
- resistance = recent local high cluster or 20-day high area
- if price is range-bound, show nearby band
- if trend is strong and levels are unclear, state that levels are approximate

## 12.3 UX Rule
Always explain:
- support = area where price has recently found buyers,
- resistance = area where price has recently struggled to move higher.

---

## 13. Scheduling and Timing

## 13.1 Default Schedule
- run once per trading day,
- target 60 to 90 minutes after regular market close,
- default timezone is user-configured timezone.

## 13.2 Job Flow
1. load active users,
2. check whether today is a market day,
3. verify no report already sent,
4. retrieve memory + profile + positions,
5. fetch market/news data,
6. generate report,
7. send email,
8. log delivery event.

## 13.3 Idempotency
Use unique key:
- `user_id + report_date + report_type`

If key already exists as sent, skip duplicate send.

---

## 14. API Contracts

## 14.1 EverMemOS Write
**Endpoint:** `POST /api/v1/memories`

Use for:
- storing user messages,
- storing system-authored memory notes when appropriate.

Example request:
```json
{
  "message_id": "msg_20260308_010",
  "create_time": "2026-03-08T21:00:00+00:00",
  "sender": "user_001",
  "content": "I am a beginner investor and prefer short daily summaries.",
  "user_id": "user_001",
  "group_id": "memoryvest_user_001"
}
```

## 14.2 EverMemOS Search
**Endpoint:** `GET /api/v1/memories/search`

Example request:
```json
{
  "query": "What stocks does the user care about and how much detail do they prefer?",
  "user_id": "user_001",
  "retrieve_method": "hybrid",
  "memory_types": ["episodic_memory", "foresight", "event_log"],
  "top_k": 10
}
```

Implementation note for MVP:
- because the search interface does not reliably support `profile` as a searchable memory type, keep profile facts in canonical app storage and use EverMemOS retrieval mainly for episodic, foresight, and event-log context.

---

## 15. Prompting Strategy

## 15.1 Input-to-Profile Extraction Prompt
Goal:
- convert free-form user text into structured profile/position updates.

Output schema:
- `intent`
- `profile_updates`
- `positions_to_add`
- `positions_to_update`
- `cash_update`
- `watch_intents`
- `memory_note`

## 15.2 Daily Summary Prompt
Inputs:
- canonical profile,
- canonical positions,
- retrieved memory context,
- market performance data,
- ranked news list,
- support/resistance values.

Output requirements:
- beginner-friendly,
- no financial advice,
- explicit “why it matters” reasoning,
- concise but personalized.

## 15.3 Personalization Rules in Prompt
The prompt should condition on:
- experience level,
- jargon tolerance,
- report length preference,
- interests,
- owned tickers,
- recent user concerns,
- past report topics already covered.

---

## 16. Storage Design

## 16.1 Application Database
For MVP, use SQLite or Postgres for deterministic state.

Tables:
- `users`
- `profiles`
- `positions`
- `cash_balances`
- `watch_intents`
- `report_history`
- `delivery_attempts`

## 16.2 EverMemOS Role
EverMemOS is the memory engine, not the sole source of truth for financial state.

Use it for:
- persistence of user narrative,
- continuity across conversations,
- recall of evolving intent and preferences,
- deduplication context,
- demoing long-term memory.

---

## 17. Error Handling

## 17.1 Failure Modes
- EverMemOS unavailable
- market data API unavailable
- news API rate limit
- invalid ticker input
- email send failure
- duplicate schedule execution
- incomplete memory retrieval

## 17.2 Handling Strategy
- retry transient network failures,
- fall back to canonical local state when memory retrieval is partial,
- generate reduced report if some news is unavailable,
- mark failed send in report history,
- expose clear CLI error messages.

---

## 18. Security and Privacy

## 18.1 Stored Data
Sensitive fields include:
- email address,
- portfolio holdings,
- cash amount,
- user preferences.

## 18.2 MVP Security Requirements
- store secrets in environment variables,
- never log raw credentials,
- validate and sanitize CLI input,
- encrypt or protect production database where possible,
- avoid storing unnecessary personal information,
- include clear disclaimer about informational-only nature.

---

## 19. Observability

## 19.1 Logging
Each major action should log:
- correlation ID,
- user ID,
- report date,
- external service latency,
- send outcome.

## 19.2 Metrics
Track:
- report generation success rate,
- email delivery success rate,
- average report generation latency,
- memory retrieval latency,
- number of relevant articles selected,
- duplicate suppression count.

---

## 20. Testing Strategy

## 20.1 Unit Tests
- parser/extractor logic,
- support/resistance heuristics,
- ranking logic,
- report rendering,
- scheduling idempotency.

## 20.2 Integration Tests
- EverMemOS write + search flow,
- end-to-end report generation with mocked market/news data,
- email send flow with test provider,
- CLI command workflows.

## 20.3 Demo Test Scenario
Scripted demo should show:
1. user onboarding,
2. storing memory,
3. retrieving memory,
4. generating personalized report,
5. showing “why this report” explanation,
6. sending email successfully.

---

## 21. Suggested Repository Structure

```text
memoryvest/
  app/
    cli/
      main.py
      commands_profile.py
      commands_portfolio.py
      commands_report.py
    services/
      memory_service.py
      profile_service.py
      portfolio_service.py
      market_data_service.py
      news_service.py
      analysis_service.py
      report_service.py
      delivery_service.py
      scheduler_service.py
    models/
      profile.py
      position.py
      report.py
      watch_intent.py
    prompts/
      extract_profile.txt
      generate_daily_report.txt
    infra/
      evermemos_client.py
      market_client.py
      news_client.py
      email_client.py
      db.py
    jobs/
      generate_daily_report.py
    config.py
  tests/
  scripts/
  README.md
```

---

## 22. MVP Milestones

## Milestone 1: Local CLI + EverMemOS Integration
- onboarding works,
- user messages stored in EverMemOS,
- profile/position state saved locally.

## Milestone 2: Memory-Aware Report Preview
- retrieve memory context,
- fetch mock or live market/news data,
- print personalized report in terminal.

## Milestone 3: Email Delivery + Scheduler
- send report by email,
- run on schedule,
- persist report history.

## Milestone 4: Demo Polish
- add `why-this-report`,
- suppress duplicate news,
- improve beginner-friendly tone,
- script a reliable end-to-end demo.

---

## 23. Success Criteria

The MVP is successful if:
- a new user can onboard through the CLI in under 5 minutes,
- EverMemOS stores and later recalls relevant user context,
- the generated report clearly reflects remembered preferences and holdings,
- the report is understandable to a beginner,
- the system sends one reliable daily email,
- the demo clearly shows why memory makes the product better than a generic stock newsletter.

---

## 24. Future Extensions
- weekly recap mode,
- richer portfolio analytics,
- sentiment and earnings calendar integration,
- user-specific alert thresholds,
- web dashboard,
- conversational report Q&A,
- compare today’s report to last week’s remembered concerns,
- watchlist coaching and educational mode.

---

## 25. Implementation Notes for Agentic Development

This project is suitable for Cursor-style agentic development if work is split into bounded modules with explicit contracts.

Recommended implementation order:
1. scaffold CLI and config,
2. implement local profile/portfolio storage,
3. implement EverMemOS client,
4. implement parsing/extraction flow,
5. implement market/news clients,
6. implement report generator,
7. implement email delivery,
8. implement scheduler,
9. add tests and demo script.

Recommended agent tasks:
- “Implement Typer CLI with onboarding and portfolio commands”
- “Implement EverMemOS client with store/search methods”
- “Implement parser for free-form investing profile updates”
- “Implement report generation service with strict output schema”
- “Implement daily scheduler job with idempotency checks”
- “Implement support/resistance heuristic over daily candles”

The repository should enforce strong schemas and narrow service interfaces so agent-generated code remains composable and testable.

