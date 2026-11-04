AMINA JOB 2: documents, payments and appointment

Files:
- seeding/seed_amina_documents_payments_appointment.sql
- seeding/tests/check_amina_documents_payments_appointment.sql

Run in pgAdmin:
1. Connect to your project database (with tables, foreign keys and checks installed).
2. Open the seed SQL in Query Tool. Execute the ENTIRE file, including BEGIN/COMMIT.
3. Open the check SQL and execute it. Messages should report PASS.
4. Rerun the seed if needed: every insert uses ON CONFLICT DO NOTHING.
   If execution stops in a failed transaction, run ROLLBACK; before retrying.

psql alternative, from the repository root:
psql -v ON_ERROR_STOP=1 -d YOUR_DATABASE -f seeding/seed_amina_documents_payments_appointment.sql -f seeding/tests/check_amina_documents_payments_appointment.sql

Your five owned rows, exactly as supplied:
- Amina passport VERIFIED by Brian, 842000 bytes, 2026-10-06 09:30+03.
- Amina national ID PENDING, 310000 bytes, no verification fields.
- UGX 50000 MTN MoMo COMPLETED, MTN-20261003-0001, 2026-10-03 10:00/10:02+03.
- UGX 20000 MTN MoMo PENDING, 2026-10-07 12:00+03, no reference/completion.
- Document submission with Grace, 2026-11-02 10:00+03, UPCOMING.

The unchanged base block from seed base block.pdf is included, followed by the
three parent rows (Amina user/profile/application). All UUIDs follow SEEDING POLL.pdf.
The application is inserted at Registered only if absent; an existing final stage
is not reset. Roles/stages are looked up by names/order, never assumed numeric IDs.
Your file inserts no explicit stage history, notifications or audit rows. The
application/history and notification/audit owners retain their jobs. Historical
VERIFIED/COMPLETED states are inserted directly, so UPDATE-only audit triggers
will not create extra rows assigned to the audit seed owner.

Validation performed in a separate PostgreSQL 18 test instance:
- Alone on the tables/relationships/checks baseline, with document/appointment
  role triggers, document/payment audit triggers, refund trigger and payment checks.
- Rerun: zero inserted rows, all values unchanged.
- Simulated owner advancing Amina to stage 3, followed by rerun: stage 3 preserved.
- Shared base block matches the extracted source unchanged.
No changes were made to the real pgAdmin database.

Team integration notes (other members' files were NOT edited):
- Current seed_cathy_story.sql still generates UUIDs instead of using the fixed
  shared sheet. Its owner must align it before full six-file order independence
  can be verified. Do not combine old random-ID data with the new fixed-ID seeds.
- All six seed files are not available yet, so all-six permutations/49-row totals
  are not claimed as tested. The standalone baseline has 28 rows including parents
  and base, before any automatic initial stage-history entry.
- If the automatic initial-history trigger is installed, from_stage_id must allow
  NULL, as the assignment requires. The current table file still says NOT NULL;
  the schema/history owner must resolve that existing mismatch. This seed neither
  changes schema nor disables triggers. That optional trigger was not included in
  the baseline validation because of this mismatch.
- Your seed does not update existing rows. If an existing fixed UUID has different
  data, the read-only checker reports the mismatch instead of overwriting it.
