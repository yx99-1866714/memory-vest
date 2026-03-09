Write-Host "========================================="
Write-Host "   MemoryVest MVP Demo Script (Windows)  "
Write-Host "========================================="
Write-Host ""
Write-Host "1. Initializing the Database..."
uv run memoryvest init
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================="
Write-Host "2. Showing the Chat workflow (Simulated)"
Write-Host "This simulates a user providing profile and portfolio information."
Write-Host "Normally run via: uv run memoryvest chat"
Write-Host "========================================="
Write-Host ""

Write-Host ">>> Let's assume the user chatted and we extracted their profile."
Write-Host ">>> Now let's preview the personalized MemoryVest report."
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "========================================="
Write-Host "3. Generating Report Preview"
Write-Host "uv run memoryvest report preview"
Write-Host "========================================="
Write-Host ""

# Note: The DB is empty if we didn't chat, so we need to mock a profile.
# We'll use SQLite to inject a mock profile for the demo so preview works immediately.
sqlite3 memoryvest.db "INSERT OR REPLACE INTO profiles (user_id, email, experience_level, risk_tolerance, explanation_style, jargon_tolerance, report_frequency, report_length, timezone, interests, sector_preferences, alert_sensitivity) VALUES ('user_001', 'demo@memoryvest.local', 'beginner', 'low', 'plain_english', 'low', 'daily', 'short', 'UTC', '[\"AI\", \"gaming\"]', '[\"technology\"]', 'high');"
sqlite3 memoryvest.db "INSERT OR REPLACE INTO positions (user_id, ticker, shares, avg_cost, opened_at, status) VALUES ('user_001', 'AAPL', 10, 150.0, '2026-03-01', 'open');"
sqlite3 memoryvest.db "INSERT OR REPLACE INTO cash_balances (user_id, available_cash, currency, updated_at) VALUES ('user_001', 5000.0, 'USD', '2026-03-08');"

uv run memoryvest report preview --user-id "user_001"

Write-Host ""
Write-Host "Demo complete! To run manually:"
Write-Host "uv run memoryvest chat"
Write-Host "uv run memoryvest report preview"
