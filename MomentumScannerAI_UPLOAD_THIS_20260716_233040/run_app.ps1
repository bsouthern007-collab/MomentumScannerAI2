Set-Location -LiteralPath $PSScriptRoot
$logFile = Join-Path $PSScriptRoot "data\streamlit.log"
& "$PSScriptRoot\.venv\Scripts\python.exe" -m streamlit run "$PSScriptRoot\app.py" --server.port 8502 --server.address localhost --server.headless true --browser.gatherUsageStats false *> $logFile
