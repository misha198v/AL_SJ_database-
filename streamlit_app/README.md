# ALSJ Travel Agency Portal (Streamlit)

A role-based web portal on top of the PostgreSQL travel-agency database. It replaces the
Django UI with Streamlit and adds live dashboards, table browsing with CRUD, an ERD,
a data dictionary and a 7-stage application workflow.

## What it does

| Role | Can do |
|---|---|
| **Client** | Sees *only* their own application: live stage tracker, upload documents, pay by mobile money, own appointments and notifications |
| **Secretary** | Adds clients, registers applications, assigns Field Agents, books appointments, sends notifications, read-only table browser |
| **Field Agent** | Sees assigned applications and clients, verifies/rejects documents, moves stages |
| **Data Entry Staff** | All applications, verifies documents, confirms payments (simulated provider), moves stages |
| **Director** | Everything above that the database allows, plus employees, analytics, audit trail, table CRUD, ERD, data dictionary, system flow |

Login is a **demo role switcher** (no passwords): pick a role, pick a person.
Permissions are still enforced: menus are filtered per role and every page re-checks access.
Database triggers add a second layer (for example only Field Agents and Data Entry Staff
can verify documents; `audit_logs`, `stage_history` and `pipeline_stages` cannot be edited).

## Project layout

```
streamlit_app/
├── app.py                  # entry point: login, role menu, notification bell
├── requirements.txt
├── .streamlit/
│   ├── config.toml         # theme (light, monospace)
│   ├── secrets.toml        # YOUR database credentials (not in git)
│   └── secrets.toml.example
├── utils/
│   ├── db.py               # SQLAlchemy engine, fetch/execute, transactions
│   ├── auth.py             # roles, permissions, demo login, page guard
│   ├── schema.py           # reads tables, keys, enums from the DB catalog
│   ├── notify.py           # notifications + read tracking
│   ├── app_detail.py       # shared application workspace
│   ├── people.py           # create clients / employees
│   └── ui.py               # shared widgets and error handling
├── views/                  # one file per page
└── uploads/                # uploaded documents (local, not in git)
```

## Setup

You need: **Git**, **Python 3.11+**, **PostgreSQL 14+** (running locally).

### 1. Get the code

```bash
git clone https://github.com/Raheem840/AL_SJ_database-.git
cd AL_SJ_database-
git fetch origin
git checkout streamlit_ui
cd streamlit_app
```

Already cloned? Just run `git fetch origin && git checkout streamlit_ui && git pull`.

### 2. Get the database

Your app needs the same database you hve been using earlier, so remember the database credentials for the next step


### 3. Create a virtual environment and install packages

```bash
python3 -m venv .venv
source .venv/bin/activate        # fish shell: source .venv/bin/activate.fish
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Add your database credentials

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` with your real values. Special characters (`@`, `:`, `#`) in
the password are fine. Never commit this file.

### 5. Run it

Always run from inside `streamlit_app/`:

```bash
streamlit run app.py
```

Open http://localhost:8501. On the first run the app adds two columns
(`created_at`, `read_at`) to `notifications`; your database user must own that table.

## Try it: one client through all 7 stages

Use two browser windows (one for staff roles, one for the Client).

1. **Director** → Employees → add a Field Agent and a Data Entry Staff member (if none exist).
2. **Secretary** → Clients → add a client. Applications → New application → assign the Field Agent.
3. **Client** (click *Refresh people list* on the login screen first) → My Application → upload documents.
4. **Field Agent** → Documents → reject one with a reason, verify the rest. The client gets a notification (🔴 in the menu and sidebar).
5. **Client** → re-upload the rejected document → **Field Agent** verifies it.
6. **Field Agent** → Applications → open it → Manage → move stages 2 to 7. The client's tracker updates live.
7. **Client** → Payments → pay. **Data Entry Staff** → Payments → Complete.
8. **Secretary** → Appointments → book one; Notifications → send a message.
9. **Director** → Analytics, Audit & History, ERD, System Flow.

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'utils'` | You are in the wrong folder. `cd streamlit_app` and run `streamlit run app.py` |
| `streamlit: command not found` | The venv is not active: `source .venv/bin/activate` |
| `StreamlitSecretNotFoundError` | Create `.streamlit/secrets.toml` from the `.example` file (step 4) |
| `connection refused` on port 5432 | PostgreSQL is not running: `sudo systemctl start postgresql` and check `ss -ltnp \| grep 5432` |
| `password authentication failed` / `role "x" does not exist` | Create the role: `sudo -u postgres createuser --interactive`, then `sudo -u postgres psql -c "ALTER USER x WITH PASSWORD '...';"` and update `secrets.toml` |
| `database "..." does not exist` | Create it and restore the dump (step 2) |
| `relation "..." does not exist` or `function change_stage` errors | The database was not fully restored. Restore the dump instead of building tables by hand |
| `pg_config executable not found` while installing | Install build tools: `sudo apt install libpq-dev python3-dev gcc` (Debian/Ubuntu), or use Python 3.12/3.13 |
| `collation version mismatch` warning | Harmless. Optional: `ALTER DATABASE <db> REFRESH COLLATION VERSION;` |
| `must be owner of table notifications` at start | Run once as the table owner: `ALTER TABLE notifications ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(); ALTER TABLE notifications ADD COLUMN IF NOT EXISTS read_at timestamptz; UPDATE notifications SET read_at = now() WHERE read_at IS NULL;` |
| New user missing from the login dropdown | Click **Refresh people list** (the list is cached for 60 s) |
| `StreamlitDuplicateElementKey` | A page file contains its code twice. Check with `grep -n "render_application" views/*.py` and keep one copy |
| Document download says "not stored on this machine" | `uploads/` is local and not in git. Re-upload the file on your machine |
| Port 8501 already in use | `streamlit run app.py --server.port 8502` |
| `git checkout streamlit_ui` says pathspec did not match | Run `git fetch origin` first |
| Role shows a yellow warning on the login screen | Add its upper-cased key (spaces to `_`) to `ROLE_ACCESS` in `utils/auth.py` |

## Team rules

- Work on a branch, never commit `secrets.toml`, `.venv` or `uploads/`.
- Pull before you start: `git pull origin streamlit_ui`.
- If you add a table, the Table Viewer, Data Dictionary and ERD pick it up automatically.
- New page: create `views/<name>.py`, call `guard("<name>")` first, register it in `app.py`
  and add it to `ROLE_ACCESS` in `utils/auth.py`.