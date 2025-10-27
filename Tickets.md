Tickets
========

Ziel: Konkrete, umsetzbare Tickets, damit die Implementierung sofort starten kann. Aktueller Stand: Repo enthält nur `LICENSE`; `Readme.md` und `Playbook.md` sind leer. Dieser Plan führt vom leeren Repo zum lauffähigen Grundgerüst mit Qualitätssicherung.

Hinweise
- Priorität: P0 (kritisch), P1 (hoch), P2 (normal)
- Aufwand: S (0.5–1d), M (1–2d), L (3–5d)

T-000 Scope & MVP definieren (P0, S)
- Ergebnis: Knappe Beschreibung des Produkts, Zielgruppe, 3–5 Kernziele, MVP-Umfang, Nichtziele
- Akzeptanzkriterien:
  - `Readme.md` enthält Projektbeschreibung, MVP-Ziele, grobe Architektur-Skizze
  - Liste der ersten 3–5 User Stories mit Akzeptanzkriterien

T-001 Tech-Stack-Entscheidungen dokumentieren (P0, S)
- Ergebnis: Entscheidung für Programmiersprache, App-Typ (HTTP-API vs. CLI), Paketmanager, Test-Framework, Lizenz- und Security-Vorgaben
- Akzeptanzkriterien:
  - `Playbook.md` Abschnitt „Entscheidungen“ mit: Sprache, Framework, Build, Test, Lint, Format, CI, Deployment-Ziel
  - Falls bis Entscheidungsdatum keine Präferenz: Default auf HTTP-API in Node.js (Express) ODER Python (FastAPI) festhalten und begründen

T-010 Repository-Grundgerüst anlegen (P0, S)
- Ergebnis: Ordnerstruktur und Basiskonventionen
- Akzeptanzkriterien:
  - Verzeichnisstruktur: `src/`, `tests/`, `docs/`, `.github/`
  - `.gitignore` erstellt (passend zum Stack)
  - Initiale Paket-/Projektdatei (z. B. `package.json` oder `pyproject.toml`)

T-011 Umgebungsvariablen und `.env.example` (P0, S)
- Ergebnis: Einheitliches Config-Handling
- Akzeptanzkriterien:
  - `.env.example` mit kommentierten Keys (z. B. `PORT`, `LOG_LEVEL`)
  - Code lädt Config aus ENV; Start schlägt fehl mit hilfreicher Meldung, wenn Pflichtwerte fehlen

T-012 Linting und Formatierung (P1, S)
- Ergebnis: Einheitlicher Stil und schnelle Qualitätschecks
- Akzeptanzkriterien:
  - Linter + Formatter konfiguriert (z. B. ESLint + Prettier oder Ruff/Black)
  - `npm run lint && npm run format` oder äquivalente Befehle vorhanden

T-013 Pre-commit Hooks (optional) (P2, S)
- Ergebnis: Schnelle lokale Checks vor Commits
- Akzeptanzkriterien:
  - Husky / lefthook / pre-commit konfiguriert für Lint, Format und Tests (stubs okay)

T-014 CI: Lint und Tests (P0, S)
- Ergebnis: Automatische Pipeline bei PRs
- Akzeptanzkriterien:
  - GitHub Actions Workflow unter `.github/workflows/ci.yml`
  - Job führt Lint, Format-Check und Tests aus

T-020 Hello-World Service (HTTP-API, Default) (P0, S)
- Ergebnis: Startfähige App mit Health Endpoint
- Akzeptanzkriterien:
  - Startskript: `npm run start` oder äquiv. (z. B. `uvicorn app:app --reload`)
  - `GET /health` liefert `200 OK` mit `{ status: "ok", version }`
  - Logs beim Start mit Port und Environment
  - Alternativ (falls CLI gewählt): Kommando `hector hello` gibt Gruß + Version aus, Exit-Code 0

T-021 Basis-Routing/Kommandostruktur (P1, S)
- Ergebnis: Struktur für zukünftige Endpunkte/Kommandos
- Akzeptanzkriterien:
  - Trennung von Entry-Point, Routing/CLI-Parser und Business-Logik
  - Erste, leere Handler/Kommandos angelegt mit TODO-Kommentaren

T-022 Fehlerbehandlung und Logging (P1, S)
- Ergebnis: Vorhersehbares Fehlerverhalten und brauchbare Logs
- Akzeptanzkriterien:
  - Zentrales Error-Handling (HTTP: 4xx/5xx konsistent; CLI: Exit-Codes)
  - Logger mit Leveln (debug, info, warn, error) und korrelierenden Request-IDs (HTTP)

T-030 Tests: Grundsetup und Smoke-Test (P0, S)
- Ergebnis: Test-Framework + erster Test läuft in CI
- Akzeptanzkriterien:
  - Test-Runner konfiguriert (z. B. Vitest/Jest bzw. Pytest)
  - Smoke-Test: Health-Endpoint (oder CLI-Kommando) testet Exit-Code/Status 200

T-031 Security-Baseline (P1, S)
- Ergebnis: Minimaler Schutz vor gängigen Risiken
- Akzeptanzkriterien:
  - Abhängigkeitsprüfung (z. B. `npm audit`/`pip-audit`) in CI
  - `SECURITY.md` mit Meldeweg
  - Optional: `CODEOWNERS` gepflegt

T-040 Readme befüllen (P0, S)
- Ergebnis: Schnellstart für Entwickler:innen
- Akzeptanzkriterien:
  - Projektbeschreibung, Setup-Schritte, Starten/Tests, ENV-Variablen, Architektur-Übersicht
  - Verweis auf `Playbook.md` für Prozesse/Entscheidungen

T-041 Playbook befüllen (P1, S)
- Ergebnis: Arbeitsweise und Entscheidungen dokumentiert
- Akzeptanzkriterien:
  - Bereiche: Entscheidungsprotokoll (ADR light), Branch-/Release-Strategie, Code-Style, PR-Checkliste

Backlog-Vorlage (für neue Features)
- Titel im Format: `F-XXX Kurzbeschreibung`
- Inhalt: Problem, Zielbild, Akzeptanzkriterien (Given/When/Then), Abhängigkeiten, Risiken, Messbare Metriken

Nächste Schritte (Empfehlung)
1) T-000, T-001 abschließen (Entscheidungen) – max. 0.5–1d
2) T-010, T-011, T-014 umsetzen – Repo lauffähig machen
3) T-020, T-030 liefern – „Hello World“ + Smoke-Test in CI
4) T-012, T-022, T-040 nachziehen – Entwickler-Experience festigen
