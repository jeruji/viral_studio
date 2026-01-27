$envFile = ".env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match "^\s*$") { return }
    if ($_ -match "^\s*#") { return }
    $parts = $_.Split("=", 2)
    if ($parts.Length -eq 2) {
      $name = $parts[0].Trim()
      $value = $parts[1].Trim()
      if ($name.Length -gt 0) {
        Set-Item -Path "Env:$name" -Value $value
      }
    }
  }
}

uvicorn api.main:app --host 0.0.0.0 --port 8000
