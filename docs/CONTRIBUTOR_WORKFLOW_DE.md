# Contributor Workflow — Kurzleitfaden

Ziel: Einfache, klare Anleitung für Contributor und Maintainer.

1) Branch erstellen (lokal)
- Benutze Branch‑Namen nach Konvention (siehe [BRANCHING_STRATEGY.md](BRANCHING_STRATEGY.md)).
- Beispiele: `feature/...`, `bugfix/...`, `docs/...`, `chore/...`.

2) Lokal vorbereiten
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_dev.txt
pip install -r requirements_style.txt
pre-commit install
```
- Führe `pre-commit run --all-files` aus und behebe Fehler lokal.

3) Änderungen committen
- Schreibe aussagekräftige Commits: `feat: ...`, `fix: ...`, `docs: ...`.
- Formatieren: `black . && isort .` oder `pre-commit run --all-files`.

4) Push & PR öffnen
- `git push origin feature/...`
- Öffne eine PR gegen `main` und fülle das PR‑Template aus (Beschreibung, Tests, Checklist).

5) Welche Pipelines laufen?
- Push/PR: schnelle `preflight` + `fast checks` (black/isort + smoke tests).
- Vollständige QA Matrix läuft nur nach Label oder `/run-qa-matrix` Kommentar.

6) Reviews & Merge
- Mindestens 1 Approval erforderlich (Branch‑Protection).
- Merge nur wenn Fast Checks grün; für größere Änderungen: QA Matrix anfordern.

7) Maintainer / Release
- Releases nur von Maintainer: `manifest.json`, `CHANGELOG.md`, `RELEASE_NOTES.md` updaten.
- Vor Release: `./scripts/release_automation.sh --dry-run` ausführen.

Troubleshooting (Kurz)
- `black --check`/`isort --check-only` fehlschlägt → lokal `black .` / `isort .` ausführen.
- Smoke‑Tests fehlschlagen → `pytest tests/ -v` lokal ausführen, Fehler beheben.

Weitere Infos
- Tests: [TESTS.md](TESTS.md)
- Branching: [BRANCHING_STRATEGY.md](BRANCHING_STRATEGY.md)

Bei Fragen: PR kommentieren oder Issue öffnen.
