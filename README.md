## Django (folder `backend/` in the repo)
- venv + `requirements.txt`; `.env` holds DB settings (never committed); Django's own tables live in schema `django` (`search_path=django,public`), our 12 tables stay in `public`.
- `core/models.py` comes from `inspectdb` (unmanaged). Never hand-edit it; regenerate when tables change. New views/reports need no Django change (query with `fetch_all`).
- Login: phone + bcrypt against OUR `users` table, session holds id, name, role. Role guard: `@role_required('Director', ...)`.
- Old users: `python manage.py set_password ChangeMe123! --all` (dev), or `... NewPass123 <phone>`.
- Files: `db.py auth.py decorators.py context.py (menus) views.py (login, register) pages.py (lists, dashboard, all-tables browser, CSV) actions.py (all forms) urls.py management/commands/set_password.py` + templates.
## What each role can do
- **Director**: dashboard (12 KPIs, stage bars, 5 reports), applications, transactions (filter by status), employees with their assigned clients, clients, documents, appointments, notifications, stage history, audit log, users, all 12 tables (+CSV); forms: add client, add employee, new application (assign agent), send notification, payment actions, stage moves, document decisions.
- **Secretary**: applications, clients, add client, new application, appointments (book, complete, cancel), send notification.
- **Field Agent**: "My clients" (contact details), assigned applications, verify/reject documents, move stage.
- **Data Entry Staff**: applications, documents, verify/reject, move stage, payment actions.
- **Client**: register, new application, upload document (PDF/JPG/PNG, max 5 MB), pay (simulated MTN/Airtel), see own applications, stage, history. Cannot open other clients' applications.
## Test logins (password Tes1234! after set_password)
Director Moses 0700000004, Secretary Grace 0700000003, Field Agent Brian 0700000001, Data Entry Diana 0700000002, clients Amina 0772556213, Cathy 0700000012, Daniel 0700000013.
