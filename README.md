# MemoryVest

Beginner-Friendly Investing Companion MVP

MemoryVest is a CLI-based investing companion for everyday users. It uses EverMemOS as its long-term memory layer to securely track your investment profile, portfolio holdings, and future interests.

## Features

- Uses conversational memory (EverMemOS) to learn your preferences.
- Tracks cash and stock positions.
- Generates a beginner-friendly daily stock report using LLMs (OpenAI or OpenRouter).
- Sends formatted email reports.

---

## Interactive Chat Mode

The core experience of MemoryVest is designed around a natural language assistant. You do not need to learn complex commands to update your portfolio or set your preferences.

1. **Initialize the database**
   Run this once to set up your local storage schemas.
   ```bash
   uv run memoryvest init
   ```

2. **Start chatting**
   Enter the chat loop. The assistant will parse your natural language sentences and automatically update your profile, portfolio, and cash balance under the hood. 
   ```bash
   uv run memoryvest chat --user-id "my_username"
   ```

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

## Explicit Commands

If you prefer to skip the chat layer and operate the daily report manually, you can use the report generation commands:

***Generate a Preview***
Prints the personalized report output directly to your terminal screen for the specified user.
```bash
uv run memoryvest report preview --user-id "user_001"
```

***Send Email***
Generates the report and fires an email payload to the user's saved email address based on your `.env` SMTP variables.
```bash
uv run memoryvest report send --user-id "user_001"
```

## Debugging

You can append the `--verbose` or `-v` flag to any command to enable trace logging. This is incredibly helpful for seeing exactly what data is being sent to the LLMs and what raw JSON they are returning.

```bash
uv run memoryvest --verbose chat
uv run memoryvest --verbose report preview
```
