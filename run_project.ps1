Write-Host "Starting AI Disaster Intelligence Platform..." -ForegroundColor Green

$projectPath = (Get-Location).Path

# 1. Start FastAPI Backend
Write-Host "1. Starting FastAPI Backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"Set-Location '$projectPath'; `$env:PYTHONPATH='$projectPath'; .venv\Scripts\python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload`""

# Wait for backend to be ready
Start-Sleep -Seconds 4

# 2. Start Streamlit Dashboard
Write-Host "2. Starting Streamlit Dashboard..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"Set-Location '$projectPath'; `$env:PYTHONPATH='$projectPath'; .venv\Scripts\python -m streamlit run dashboard/streamlit_dashboard.py`""

# 3. Start Telegram Bot
Write-Host "3. Starting Telegram Bot Engine..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"Set-Location '$projectPath'; `$env:PYTHONPATH='$projectPath'; .venv\Scripts\python telegram_bot/bot.py`""

# 4. Start ML Data Scheduler
Write-Host "4. Starting Background Alert & Data Scheduler..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"Set-Location '$projectPath'; `$env:PYTHONPATH='$projectPath'; .venv\Scripts\python src/scheduler.py`""

Write-Host "All components launched successfully in separate windows!" -ForegroundColor Cyan
