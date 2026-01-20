# /update-docs

Use the doc-updater agent to sync documentation with recent changes.

Steps:
1) Scan code/tests for behavior or API changes (services, diagnostics, config flow).
2) Update README/INSTALLATION/CHANGELOG and relevant docs under docs/.
3) Note verification commands (pytest, black, isort) and any migration steps.
