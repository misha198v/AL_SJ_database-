# AL SJ travel workspace

The premium Django interface is integrated in this project folder on
`feat/premium-django-ui`. See [RUN_LOCALLY.md](RUN_LOCALLY.md) to start it.

# Django integration

This branch connects the Django prototype to the existing PostgreSQL permissions.
See [backend/README.md](backend/README.md) for setup and verification.

Django sessions and migration records live in SQLite. Business data stays in the
existing PostgreSQL database. Login returns only a safe identity from a narrow
database routine. Each authenticated request sets its database role and actor
locally inside one PostgreSQL transaction.

Enabled capabilities follow the installed permission scripts:

- Data Entry Staff: pending document queue, time-per-stage report/CSV, application
  reads, document decisions and stage changes through the existing routines.
- Field Agent: assigned applications/documents, decisions and stage changes.
- Secretary: appointment reads, creation, completion, cancellation and deletion
  through the existing appointment routines.
- Director: read-only dashboard, lists, reports and safe table/CSV browsing.
- Client: own applications, documents, payment information and current stage.

The prototype previously offered additional writes without matching database
permissions. Registration, new applications, employee/client creation, assignment,
uploads, simulated payments, notifications and bulk password resets are disabled.
They require separately agreed, narrowly scoped routines before being enabled.
No existing database permission is broadened to support those forms.

Passwords are not reset by setup. The advertised demo password works only if it
matches the hashes already stored in your database.
