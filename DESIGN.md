---
version: alpha
name: "AL SJ Journey Workspace"
description: "A composed travel operations workspace inspired by flight manifests and itinerary maps."
colors:
  primary: "#126D76"
  primary-hover: "#0B555D"
  ink: "#162C43"
  nav: "#0D2639"
  background: "#F2F6F8"
  surface: "#FFFFFF"
  muted: "#586C7A"
  border: "#DCE6EB"
  accent-soft: "#E5F2F1"
  gold: "#B58741"
  warning: "#8A5B16"
  warning-soft: "#FFF3DA"
  danger: "#A53545"
  danger-soft: "#FCECF0"
  success: "#25684D"
  success-soft: "#E6F4ED"
typography:
  display:
    fontFamily: "Outfit, Bahnschrift, sans-serif"
  sans:
    fontFamily: "Manrope, Aptos, Segoe UI, sans-serif"
  mono:
    fontFamily: "Consolas, monospace"
rounded:
  DEFAULT: "0.75rem"
  sm: "0.5rem"
  lg: "1.25rem"
spacing:
  page-max: "96rem"
  section-gap: "2rem"
components:
  button: {}
  card: {}
  table: {}
  field: {}
  dialog: {}
---

# AL SJ Journey Workspace Design System

## Overview

### Creative North Star
A flight manifest beside a carefully composed travel itinerary. The signature is
a seven-stop journey rail showing real pipeline progress, echoed by a route line
on the public welcome page. It represents the actual seven project stages.

### Product context and register
Ugandan travel agency staff and clients use English on desktop and phone.
The staff register prioritizes clear decisions and dense, legible information.
The public welcome and sign-in pages use the same identity with more expressive
typography. Time is Africa/Kampala, Gregorian; amounts remain in their recorded
currency. No Japan-market or Japanese locale scope is present.

Avoid generic neon SaaS gradients, invented performance claims, glass panels
over operational data, fake notifications, and decorative charts without data.
Navy navigation frames a pale blue workspace; teal marks the primary action.
Use the display type sparingly for page headings and numbers.

Runtime ownership is Model B: backend/core/static/core/tokens.json is canonical;
backend/scripts/generate_tokens.py generates tokens.css. This file mirrors that
source. verify_ui.py checks the CSS and design values for drift.

## Colors
Frontmatter values map one-to-one to --color-NAME. Text uses ink or muted;
navigation uses nav and surface. Pending, error and success use labeled badges
with the corresponding semantic foreground/background pairs. Primary and focus
use teal. Gold is decorative and never the sole indicator of a state.

## Typography
Manrope is the body and dense table face, Outfit the display and brand face.
Local font files are preferred; named Windows/system fallbacks keep the app
usable offline. Body is 14px with 1.6 line height; controls are at least 14px.
Numbers use tabular figures. Data identifiers use Consolas and remain selectable.
Headings use sentence case. Do not shrink the working table below 13px.

## Layout
Use a 248px navy sidebar, 80px top bar and a generous 32px content inset.
Content width is bounded by page-max. The 8px rhythm expresses the user's
requested unified design. At 1080px use a slimmer sidebar; below 760px collapse
navigation into an explicitly expanded menu above natural-height page content.
Tables own horizontal overflow; forms use document scrolling, never a clipped
viewport. Page-level headings and toolbars wrap before they collide.

## Elevation & Depth
White bordered surfaces are the main structural layer. Shadows are reserved
for the dialog and a restrained sign-in panel. Avoid blur on operational data.
The supported theme is light, with a contrasting dark navigation frame.

## Shapes
Use the exact rounded tokens. Cards use lg, controls use sm; badges are pills.
Status dots accompany readable text. Icons share 24px viewboxes, 1.7px strokes,
rounded caps and no ambiguous icon-only business actions.

## Components
Buttons use one solid primary action and outline/ghost secondary actions.
All enabled actions have hover, focus-visible and busy states. Busy labels
preserve geometry and announce progress. Disabled controls cannot submit.

Navigation, page headings, cards, form fields, table toolbar and pager are shared.
A table header is sticky inside its visible horizontal-scroll surface. Search
and filters use committed URL state, with explicit Clear search and reset links.
No selection checkboxes are presented because bulk actions are not authorized.

Fields have labels and visible help/error text. Native selects and the native
datetime-local picker deliberately retain platform-owned popups. Passwords are
masked, with an accessible Show password control. Error summaries receive focus.
Forms preserve non-sensitive input and block duplicate submissions. A native
dialog provides application-owned deletion and stage confirmation, Escape,
focus trapping, safe initial focus and return to the original control.

Motion lasts 140–220ms for feedback; there is no ambient animation in data views.
Respect prefers-reduced-motion. Charts are real labeled bars with text tables;
no fabricated KPI values. Content names the task, object and result.

## Do's and Don'ts
- Do keep document queue ordering oldest-first and use existing report calculations.
- Do retain all permission guards and read-only Director presentation.
- Don't hide errors solely in transient notifications.
- Don't add actions for which the database grants no authority.
