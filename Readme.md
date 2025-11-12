Hector Service
==============

Hector ist ein leichtgewichtiges FastAPI-Backend, das als Ausgangspunkt fuer interne Tools dient. Der Fokus liegt auf schneller Iteration, klarer Observability und einem sauberen Entwicklungsprozess.

## Scope und Ziele (T-000)

- **Zielgruppe**: Produkt- und Entwicklungsteams, die kurzfristig eine HTTP-API fuer Experimentierung benoetigen.
- **Problem**: Idee validieren, ohne Infrastruktur von Grund auf aufzubauen.
- **Loesungsversprechen**: Bereitstellung eines produktionstauglichen Skeletons mit Health-Monitoring, Logging und Tests.
- **MVP-Ziele**:
  1. Bereitstellung eines stabilen Health-Endpunkts fuer Monitoring.
  2. Konsistente Konfiguration ueber Umgebungsvariablen.
  3. Basis-Observability durch strukturierte Logs und Request-IDs.
  4. Entwicklerfreundliche DX (Lint, Format, Tests, CI) ab Tag 1.
- **Nichtziele**:
  - Persistente Speicherung oder Datenbankanbindung.
  - Benutzer-Management oder Authentifizierung.
  - Frontend-UI.

## MVP User Stories

1. **US-001 Monitoring**
   - Given der Service laeuft,
   - When ein Operator `GET /health` aufruft,
   - Then erhaelt er Status `ok`, Environment, Version und eine Request-ID.

2. **US-002 Konfigurierbarkeit**
   - Given ich habe eine `.env` mit Projektwerten angelegt,
   - When ich den Service starte,
   - Then nutzt der Dienst diese Werte und bricht mit Hinweis ab, falls Pflichtwerte fehlen.

3. **US-003 Logging**
   - Given eine Anfrage wird verarbeitet,
   - When der Service startet und Requests annimmt,
   - Then werden Logs im Format `timestamp | level | logger | message` mit Request-ID erzeugt.

4. **US-004 Qualitaetssicherung**
   - Given ein Pull Request wird erstellt,
   - When die CI-Pipeline laeuft,
   - Then schlagen Lint, Format-Check, Typpruefung und Tests fehl, falls Verstosse auftreten.

## Architektur-Ueberblick

- **FastAPI Application Factory** (`src/hector/app.py`): erzeugt die ASGI-App und registriert Router.
- **Konfigurationslayer** (`src/hector/config.py`): zentrale Settings per Pydantic, laedt `.env`/ENV.
- **Middleware** (`src/hector/middleware.py`): vergibt Request-IDs fuer Traceability.
- **Router** (`src/hector/routers/`): modulare Endpunkte, aktuell Health.
- **Entry Point** (`src/hector/main.py`): startet Uvicorn als CLI-Kommando `hector`.
- **Tests** (`tests/`): Pytest + HTTPX fuer Funktions- und Smoke-Tests.

```
Client --> Uvicorn --> FastAPI App --> Router --> (Business-Logik) --> Response
                  |              |
                  |              --> Settings / Middleware
                  --> Logging
```

## Features

- Python 3.12, FastAPI, Uvicorn (ASGI)
- Strukturierte Konfiguration ueber Pydantic Settings
- Health Endpoint mit Request-ID-Middleware
- Einheitliche Tools: Ruff (Lint & Format), MyPy, Pytest
- CI-Workflow mit GitHub Actions

## Schnellstart

```bash
# optional: uv installieren (https://github.com/astral-sh/uv)
pip install --user uv

# Abhaengigkeiten inklusive Dev-Tools installieren
uv pip install --system .[dev]

# oder isoliert entwickeln
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install .[dev]

# App starten
uv run hector

# oder direkt mit uvicorn (Hot Reload)
uv run uvicorn hector.app:create_app --factory --reload
```

Der Service lauscht standardmaessig auf Port `8000` und stellt `GET /health` bereit.

## Umgebung konfigurieren (T-011)

1. `.env.example` nach `.env` kopieren.
2. Pflichtwerte setzen:
   - `HECTOR_ENVIRONMENT` (z. B. `development`, `staging`, `production`).
   - `HECTOR_DATABASE_URL` (PostgreSQL-Verbindungsstring, z. B. `postgresql+asyncpg://user:password@localhost:5432/hector`).
3. Optionale Werte anpassen:
   - `HECTOR_PORT` fuer den HTTP-Port (Standard `8000`).
   - `HECTOR_LOG_LEVEL` (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
   - `HECTOR_DB_POOL_SIZE` (Standard `5`).
   - `HECTOR_DB_MAX_OVERFLOW` (Standard `10`).
   - `HECTOR_DB_ECHO` (Standard `false`).

Beim Start prueft der Service Pflichtwerte und bricht mit einer aussagekraeftigen Meldung ab, falls sie fehlen oder ungueltig sind.

## Datenbank-Setup und Migrationen

Das Projekt verwendet PostgreSQL mit SQLAlchemy (async) und Alembic fuer Datenbankmigrationen.

### PostgreSQL lokal aufsetzen

```bash
# Docker-Methode (empfohlen fuer Entwicklung)
docker run --name hector-postgres \
  -e POSTGRES_USER=hector \
  -e POSTGRES_PASSWORD=hector \
  -e POSTGRES_DB=hector \
  -p 5432:5432 \
  -d postgres:16-alpine

# Oder via apt/brew/etc. installieren
```

### Migrationen ausfuehren

```bash
# Virtual Environment aktivieren
source .venv/bin/activate

# Datenbank auf aktuellen Stand bringen
alembic upgrade head

# Migration-Historie anzeigen
alembic history

# Aktuelle Version anzeigen
alembic current

# Neue Migration erstellen (nach Modellaenderungen)
alembic revision --autogenerate -m "Beschreibung der Aenderung"

# Migration rueckgaengig machen
alembic downgrade -1
```

### Datenmodelle

Das Projekt definiert folgende Hauptmodelle:

- **User** (T-103): Benutzer mit Rollen (Klinikpersonal, Hundebesitzer, Admin)
- **Clinic** (T-104): Tierkliniken mit Standort und Kontaktinformationen
- **DogProfile** (T-105): Hundeprofile mit Bluttyp und Eligibilitaetspruefung
- **BloodDonationRequest** (T-106): Blutspendeanfragen mit Dringlichkeit und Status
- **DonationResponse** (T-107): Antworten von Hundebesitzern auf Anfragen

Alle Modelle befinden sich in `src/hector/models/` und nutzen:
- UUID Primary Keys
- Automatische Timestamps (created_at, updated_at)
- Async SQLAlchemy 2.0+ API
- PostgreSQL-spezifische Enums

## Qualitaetssicherung (T-012)

```bash
# Innerhalb der venv oder mit aktiviertem Python 3.12
ruff check .           # Ruff lint
ruff format .          # Ruff format (in-place)
ruff format --check .  # Format check
mypy src               # MyPy type check
pytest                 # Run tests
pip-audit              # Security audit
```

Die CI-Pipeline (`.github/workflows/ci.yml`) fuehrt dieselben Pruefungen aus und blockiert fehlerhafte Pull Requests.

### Pre-commit Hooks (T-013)

Das Projekt unterstuetzt Pre-commit Hooks fuer automatische Qualitaetschecks vor Commits:

```bash
# Pre-commit installieren (falls noch nicht geschehen)
source .venv/bin/activate
pip install pre-commit

# Hooks aktivieren
pre-commit install

# Manuell auf allen Dateien ausfuehren
pre-commit run --all-files
```

Die Hooks fuehren automatisch folgende Checks aus:
- Trailing Whitespace entfernen
- End-of-file fixer
- YAML/TOML Syntax-Check
- Ruff Linting und Formatierung
- MyPy Type-Checking

## Sicherheit (T-031)

### Dependency Scanning

Das Projekt nutzt `pip-audit` zur Pruefung auf bekannte Schwachstellen in Abhaengigkeiten:

```bash
source .venv/bin/activate
pip-audit
```

Security Audits laufen automatisch in der CI-Pipeline.

### Meldung von Sicherheitsluecken

Siehe `SECURITY.md` fuer Details zur verantwortungsvollen Offenlegung von Sicherheitsproblemen.

## Projektstruktur

```
.
├── src/hector/
│   ├── app.py          # FastAPI App Factory
│   ├── config.py       # Settings via Pydantic
│   ├── logging_config.py
│   ├── middleware.py   # Request-ID-Middleware
│   ├── routers/        # API Router Module
│   └── main.py         # uvicorn Entry Point
├── tests/              # Pytest Suites
├── docs/               # Technische Dokumente
├── .github/workflows/  # CI Pipeline
└── pyproject.toml      # Dependencies & Tooling
```

## Weiteres Vorgehen

Siehe `Tickets.md` fuer priorisierte Aufgaben und `Playbook.md` fuer Prozesse & Entscheidungen.
