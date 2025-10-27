Playbook
========

## Entscheidungsprotokoll (T-001)

| Bereich            | Entscheidung                                                                 |
|--------------------|-------------------------------------------------------------------------------|
| Sprache            | Python 3.12                                                                  |
| Framework          | FastAPI + Uvicorn (ASGI)                                                     |
| Paketmanager       | uv (fuehrt `pyproject.toml`)                                                 |
| Build              | `uv pip install --system .[dev]` fuer CI; lokal optional virtuelle Umgebung   |
| Tests              | Pytest + HTTPX AsyncClient                                                   |
| Lint/Format        | Ruff (`uv run lint`, `uv run format`)                                        |
| Typpruefung        | MyPy (`uv run typecheck`)                                                    |
| CI                 | GitHub Actions Workflow `.github/workflows/ci.yml`                           |
| Deployment         | Containerfaehig, Ziel spaeter Kubernetes/Container Apps                      |
| Security           | Abhaengigkeitspruefung via `uv run pip-audit` (folgt in separatem Ticket)    |
| Observability      | Structured Logging + Request-IDs                                             |

## Branch-Strategie

- `main`: immer releasbarer Stand.
- Feature-Branches: `feature/<ticket-id>-kurzbeschreibung`.
- Pull Requests benoetigen mindestens ein Review.

## Release-Strategie

- SemVer-Tags nach Abschluss wesentlicher Inkremente.
- Automatisches Packaging/Deployment folgt nach MVP (Ticket T-XXX geplant).

## Code-Style Richtlinien

- PEP 8 kompatibel; Formatierung erfolgt ausschliesslich mit `uv run format`.
- Typannotationen fuer Public APIs und Rueckgabewerte verpflichtend.
- Async/await fuer IO-Operationen bevorzugt.
- Keine Seiteneffekte beim Import (App nutzt Application Factory).

## Entwicklungsablauf

1. Branch vom aktuellen `main` erstellen.
2. `.env` aktualisieren (siehe `.env.example`).
3. `uv run lint`, `uv run typecheck`, `uv run test` lokal ausfuehren.
4. Pull Request eroeffnen, CI abwarten.
5. Review-Kommentare adressieren, Squash-Merge auf `main`.

## Test- und Qualitaets-Gates (T-012 Bezug)

- Pytest Tests liegen unter `tests/` und muessen in CI bestehen.
- Linting ueber Ruff, Format-Check via `uv run format:check`.
- Typpruefung mit MyPy; Fehler blocken Merge.
- Security Checks (pip-audit) werden nach Ticket T-031 integriert.

## PR-Checkliste

- [ ] Ticket referenziert, Akzeptanzkriterien erfuellt.
- [ ] Tests hinzugefuegt/geaendert und lokal bestanden (`uv run test`).
- [ ] Lint, Format und Typpruefung lokal bestanden (`uv run lint`, `uv run format:check`, `uv run typecheck`).
- [ ] Dokumentation/Readme aktualisiert, falls Auswirkungen bestehen.
- [ ] Relevante Logs/Screenshots oder API-Responses im PR beschrieben.
