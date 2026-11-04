# UX Contract

## Product context
English travel operations portal for AL SJ staff and clients in Uganda.
Africa/Kampala timezone, Gregorian dates, explicit stored currencies.
Accessibility target: WCAG 2.2 AA. Light interface and reduced-motion support.

## Business-context sources
| Domain / scope | Authoritative source | Source type | Reviewed date |
|---|---|---|---|
| Permissions | backend/README.md; migrations/roles; backend/sql/050_django_integration.sql | User-approved role rules and installed database routines | 2026-11-03 |
| Documents/stages | migrations/routines; migrations/chk_constraints; migrations/triggers | Database constraints/routines | 2026-11-03 |
| Appointments/deletion | backend/core/actions.py; approved secretary_save_appointment and secretary_delete_appointment | Existing tested capability | 2026-11-03 |
| Payments | Existing database role grants; payment check constraints | Read-only UI capability | 2026-11-03 |
| Public claims | User's project description | Project brief; no invented testimonials/prices | 2026-11-03 |

## Visual contract
DESIGN.md mirrors backend/core/static/core/tokens.json. generate_tokens.py owns
tokens.css; verify_ui.py checks drift. Shared app.css and base.html own the shell.

## Canonical UI Map
| Capability | Canonical owner | Source of truth | Allowed variants | Verification |
|---|---|---|---|---|
| Select/Listbox | shared field markup and app.css | UX-CONTRACT.md | native platform popup | browser keyboard/open popup |
| Date | shared appointment datetime-local field | UX-CONTRACT.md | native platform datetime | browser date entry and save |
| Form | app.js validation and shared form.html | UX-CONTRACT.md | login, decision, appointment, stage | unit and browser |
| Scrollbar | app.css global scrollbar tokens | DESIGN.md | horizontal table overflow | browser/computed style |
| Toast | base.html message region and inline error summary | UX-CONTRACT.md | success, info, error | live regions and focus |
| CRUD | actions.py and app.js confirm dialog | installed database routines | stay on application, return to appointments | PostgreSQL integration + browser |

Table Selection is not applicable; no bulk actions exist.

## Dataset navigation
Server-rendered search/filter/sort/page commits to URL. For the current small,
role-scoped demonstration dataset, the server filters/paginates fetched records;
large production datasets should move this step into bounded SQL queries.
Default page size is 10. Pager preserves filters, disables boundary actions,
and shows the actual matching count. Clear search is explicit and accessible.
No-results offers reset; an empty queue explains that no documents are pending.

## Flow ledger
| Operation | Trigger | Pending | Success destination | Success feedback | Failure recovery | Focus outcome | Source ref |
|---|---|---|---|---|---|---|---|
| Document decision | Verify or reject form | disable submit and busy label | application detail | decision-specific message | preserve input and inline error | summary on error | data_entry_decide_document |
| Stage change | Choose stage and confirm | disable submit | application detail | Stage updated | retain selection and show error | dialog cancel restores trigger | data_entry_change_stage |
| Appointment create | Book appointment form | disable submit | appointments | Appointment saved | preserve fields | first invalid/summary | secretary_save_appointment |
| Appointment edit | Complete/cancel | disable submit | appointments | Appointment updated | persistent error message | message region | secretary_save_appointment |
| Appointment delete | Delete and confirm | dialog explicit Delete appointment | appointments | Appointment deleted | persistent error message | safe cancel or result heading | secretary_delete_appointment |
| Search | Search/filters | page navigation | same route with URL query | matching count | reset filters | search field on clear | read-only current role |
| Sign in | phone/password | disable submit | role workspace | named account in sidebar | generic wrong password, no secret echoed | inline error summary | app_authenticate |

## Navigation and responsive behavior
Each route has a meaningful title and current navigation item. Narrow navigation
is a modeless expand/collapse region. Sidebar/footer stay in normal keyboard
order; skip link goes to main content. Tables scroll horizontally with named
regions. No critical action depends on hover. Missing/forbidden pages retain
the brand and safe navigation; permissions never rely on hidden links.

## Overlays and feedback
The shared native dialog owns confirmation, modal focus, Escape and return focus.
Delete describes appointment and consequence, initially focuses Cancel, and has
no fake Undo. Stage confirmation names the selected stage. No window.confirm,
alert or prompt. Messages are semantic live regions; errors also remain inline.

## Async and resilience
All writes are pessimistic and use the existing transaction/routine path.
No automatic retry of writes. UI disables duplicate submit; data mutations
remain atomic. Browser back/pageshow restores controls. Offline disables
mutation submission with a persistent explanation; read pages may remain visible.
Session revocation is revalidated by the existing middleware. No passwords or
business drafts are stored in localStorage. Dirty non-secret forms use an
app-owned in-app navigation warning and the browser's page-unload mechanism.
No live network search exists, so no request race/debounce owner is necessary.

## Validation and permission UI
All product forms use novalidate and shared inline validation; useful types,
required and maxlength metadata are retained. Errors expose aria-invalid and
aria-describedby. The server remains authoritative. Unsupported forms stay
unavailable. No capability is added by this redesign. Director is read-only.

## Verification
Commands: manage.py check; manage.py test core; test_integration.py against a
disposable clone; scripts/verify_ui.py; premium audit strict mode; local Playwright
UI/a11y tests. Browser matrix includes desktop 1440px, mobile 390px, keyboard,
password visibility, invalid sign-in, no-results/reset, open native controls,
confirmation cancellation, reduced motion, and actual read-only role navigation.
Compare Applications, Document queue, Time per stage and Appointments.
