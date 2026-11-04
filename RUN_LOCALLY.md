# Run the AL SJ workspace

The integrated application is in this repository's backend folder. The running
preview uses http://127.0.0.1:8001/ . An older copy may still be on port 8000.

Open the repository in VS Code, then use PowerShell:

```powershell
cd "C:\Users\Trevor\OneDrive\AL_SJ_database\AL_SJ_database-\backend"
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```

Open http://127.0.0.1:8001/login/ and use the existing website account password.
Data Entry Staff phone: 0700000002. The password in .env belongs to the database
connection; it is separate from the website password.

The existing local .env configuration, private session key and SQLite session
database were copied into this folder. They are ignored by Git. No new seed or
database setup is needed for this visual update. Do not rerun the seed scripts.

After signing in:

- Document queue shows pending documents, oldest first, with search and filters.
- Time per stage shows completed visit averages and ongoing visits separately.
- Applications has search, status filters, sorting and page navigation.
- Open an application to review documents or move its stage using your role's
  approved routines. Stage changes require confirmation.
- Director has a read-only dashboard. Secretary manages appointments, with an
  explicit confirmation before permanent deletion.

Decisions, stage changes and appointment edits affect real records when running
against the project database. Automated write tests use disposable clones only.

See backend/README.md for first-time setup on another machine. Keep .env, the
private session key and SQLite data out of Git. The shared SQL and seed files
were preserved; this branch has not been committed, pushed or merged.

## Verification

```powershell
.\backend\.venv\Scripts\python.exe backend\manage.py check
.\backend\.venv\Scripts\python.exe backend\manage.py test core
.\backend\.venv\Scripts\python.exe backend\scripts\verify_ui.py
```

Browser tests are in backend/scripts/browser_check.cjs. Install the development
dependency with npm install inside backend, then set UI_BASE_URL, UI_TEST_PASSWORD
and UI_ARTIFACT_DIR before npm run test:ui. UI_TEST_DISPOSABLE=1 allows one test
appointment creation only when UI_BASE_URL is the isolated 8011 test server.
Never run that write test against the project database.

DESIGN.md, UX-CONTRACT.md and premium-ui.json document the shared design and
interaction ownership. Font licenses are beside the self-hosted font files.
