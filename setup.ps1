# PowerShell setup script for Windows developers
# Run: .\setup.ps1 help

param(
    [string]$Command = "help",
    [switch]$Force
)

function Show-Help {
    Write-Host "Backend/DevOps Interview - Setup Commands" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🚀 FIRST TIME (Local):" -ForegroundColor Green
    Write-Host "  .\setup.ps1 env-init           Create .env files (once)"
    Write-Host "  .\setup.ps1 deps                Install dependencies (uv sync)"
    Write-Host "  .\setup.ps1 setup               deps + docker + migrate + seed (no server)"
    Write-Host ""
    Write-Host "💻 DAILY USE:" -ForegroundColor Blue
    Write-Host "  .\setup.ps1 run                 Start development server (uses .env.local)"
    Write-Host ""
    Write-Host "🔄 OTHER ENVIRONMENTS:" -ForegroundColor Yellow
    Write-Host "  .\setup.ps1 run-staging         Copy .env.staging → .env, then run"
    Write-Host "  .\setup.ps1 run-production      Copy .env.production → .env, then run"
    Write-Host ""
    Write-Host "🐳 DOCKER:" -ForegroundColor Magenta
    Write-Host "  .\setup.ps1 docker-up           Start PostgreSQL"
    Write-Host "  .\setup.ps1 docker-down         Stop PostgreSQL"
    Write-Host "  .\setup.ps1 up                  Start Postgres + web (gunicorn)"
    Write-Host "  .\setup.ps1 down                Stop all compose services"
    Write-Host ""
    Write-Host "🧪 TESTING:" -ForegroundColor Cyan
    Write-Host "  .\setup.ps1 test                Run tests (starts Postgres first)"
    Write-Host "  .\setup.ps1 check               lint + test (mirrors CI)"
    Write-Host "  .\setup.ps1 format              Format code"
    Write-Host "  .\setup.ps1 lint                Lint code"
    Write-Host "  .\setup.ps1 doctor              Toolchain and DB diagnostics"
}

function Invoke-Deps {
    uv sync
}

function Init-Environments {
    $source = ".env.example"
    if (!(Test-Path $source)) {
        Write-Host "ERROR: $source not found" -ForegroundColor Red
        exit 1
    }

    $targets = @(".env", ".env.local", ".env.staging", ".env.production")

    foreach ($target in $targets) {
        if ((Test-Path $target) -and -not $Force) {
            Write-Host "Skip $target (exists). Use -Force to overwrite."
        }
        else {
            Copy-Item $source $target -Force
            Write-Host "Created $target"
        }
    }

    Write-Host ""
    Write-Host "Environment files initialized successfully."
}

function Wait-Database {
    $attempts = 0
    $maxAttempts = 30
    while ($attempts -lt $maxAttempts) {
        docker compose exec -T postgres pg_isready -U postgres -d backend_devops_interview 2>$null
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Write-Host "Waiting for Postgres..."
        Start-Sleep -Seconds 2
        $attempts++
    }
    Write-Host "ERROR: Postgres not ready after $($maxAttempts * 2) seconds" -ForegroundColor Red
    exit 1
}

function Invoke-Migrate {
    uv run python manage.py migrate
}

function Invoke-Seed {
    uv run python manage.py seed
}

function Invoke-SeedForce {
    uv run python manage.py seed --force
}

function Start-Setup {
    Write-Host "🚀 Setting up local development..." -ForegroundColor Green
    Invoke-Deps
    Start-Docker
    Wait-Database
    Write-Host "🗄️  Running migrations..." -ForegroundColor Blue
    Invoke-Migrate
    Write-Host "📊 Seeding database (~2-3 minutes)..." -ForegroundColor Blue
    Invoke-Seed
    Write-Host ""
    Write-Host "✅ Setup complete!" -ForegroundColor Green
    Write-Host "   Run: .\setup.ps1 run"
    Write-Host "   API docs: http://localhost:8000/api/docs"
}

function Start-Dev {
    Start-Docker
    Wait-Database
    Copy-Item ".env.local" ".env" -Force
    Write-Host "🚀 Starting development server (LOCAL)..." -ForegroundColor Green
    Write-Host "API docs: http://localhost:8000/api/docs" -ForegroundColor Yellow
    Write-Host "Admin: http://localhost:8000/admin" -ForegroundColor Yellow
    Write-Host ""
    uv run python manage.py runserver
}

function Start-Staging {
    Copy-Item ".env.staging" ".env" -Force
    Write-Host "🔄 Switched to STAGING environment" -ForegroundColor Yellow
    Write-Host "⚠️  Smoke test only — not a production deployment" -ForegroundColor Yellow
    uv run python manage.py runserver 0.0.0.0:8000
}

function Start-Production {
    Copy-Item ".env.production" ".env" -Force
    Write-Host "🌍 Switched to PRODUCTION environment" -ForegroundColor Red
    Write-Host "⚠️  Smoke test only — not a production deployment" -ForegroundColor Red
    uv run python manage.py runserver 0.0.0.0:8000
}

function Start-Docker {
    Write-Host "🐘 Starting PostgreSQL..." -ForegroundColor Cyan
    docker compose up -d postgres
    Write-Host "✅ PostgreSQL starting" -ForegroundColor Green
}

function Stop-Docker {
    Write-Host "🛑 Stopping PostgreSQL..." -ForegroundColor Yellow
    docker compose stop postgres
    Write-Host "✅ PostgreSQL stopped" -ForegroundColor Green
}

function Start-All {
    docker compose up -d --build
    Write-Host "✅ Postgres + web running at http://localhost:8000" -ForegroundColor Green
}

function Stop-All {
    docker compose down
    Write-Host "✅ All services stopped" -ForegroundColor Green
}

function Run-Test {
    Start-Docker
    Wait-Database
    uv run pytest -v
}

function Run-Lint {
    uv run ruff check .
}

function Run-Format {
    uv run ruff format .
}

function Run-Check {
    Run-Lint
    Start-Docker
    Wait-Database
    uv run pytest -v
}

function Show-Doctor {
    Write-Host "=== Toolchain ===" -ForegroundColor Cyan
    try { python --version } catch { Write-Host "python: not found" }
    try { uv --version } catch { Write-Host "uv: not found" }
    try { docker --version } catch { Write-Host "docker: not found" }
    try { docker compose version } catch { Write-Host "docker compose: not found" }
    Write-Host ""
    Write-Host "=== Compose status ===" -ForegroundColor Cyan
    docker compose ps
    Write-Host ""
    Write-Host "=== Database ===" -ForegroundColor Cyan
    docker compose exec -T postgres pg_isready -U postgres 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "Postgres: ready" } else { Write-Host "Postgres: not ready (run .\setup.ps1 docker-up)" }
    Write-Host ""
    Write-Host "=== Migrations (last 5) ===" -ForegroundColor Cyan
    uv run python manage.py showmigrations --plan 2>$null | Select-Object -Last 5
}

switch ($Command) {
    "env-init" { Init-Environments }
    "help" { Show-Help }
    "deps" { Invoke-Deps }
    "sync" { Invoke-Deps }
    "wait-db" { Start-Docker; Wait-Database }
    "migrate" { Invoke-Migrate }
    "seed" { Invoke-Seed }
    "seed-force" { Invoke-SeedForce }
    "setup" { Start-Setup }
    "run" { Start-Dev }
    "run-staging" { Start-Staging }
    "run-production" { Start-Production }
    "docker-up" { Start-Docker }
    "docker-down" { Stop-Docker }
    "up" { Start-All }
    "down" { Stop-All }
    "test" { Run-Test }
    "lint" { Run-Lint }
    "format" { Run-Format }
    "check" { Run-Check }
    "doctor" { Show-Doctor }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run: .\setup.ps1 help" -ForegroundColor Yellow
    }
}
