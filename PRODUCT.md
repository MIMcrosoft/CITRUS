# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

**CITRUS** (the platform) serves two distinct audiences:
- **Coaches** (`CitrusApp`): authenticated users who manage their team's roster, schedule, and match results.
- **League members and the public** (`LigueDesPamplemousseApp`): fans, players, coaches, and prospective teams checking match schedules, standings, team rosters, league documents, and CA contact info — no login required.

## Product Purpose

CITRUS is the management and public-facing platform for the Ligue des Pamplemousses, an amateur improv (comedy) sports league organized like a real sports league: teams, divisions, scheduled matches with scores, standings, and administrative governance.

`LigueDesPamplemousseApp` specifically is the public website: it is the front door for anyone who is not a logged-in coach, and links into the authenticated `CitrusApp` (via "Citrus" in the nav) for coaches who need to log in.

## Positioning

Improv performed and scored as competitive sport: matches have final scores, teams have standings, divisions have promotion-style stakes — but the "sport" is comedic improvisation. The public site should read as a legitimate sports-league site (real standings, real schedules) while carrying the personality of an amateur comedy league, not a stiff sports-federation website.

## Operating Context

- Three divisions, each with a fixed brand color: Pamplemousse (#F05D5F), Tangerine (#F48E42), Clémentine (#F7B12F).
- League data (teams, matches, scores, standings) is real and live — sourced from `CitrusApp` models and the `Citrus_api` classement endpoint, not mocked.
- Audience is French-speaking (Québec).
- Public site sits at the site root (`/`); the coach portal lives under `/Citrus/`.

## Capabilities and Constraints

- Font is Maven Pro (Google Fonts) across the whole platform, including the public site — single-family, not up for negotiation. Hierarchy must be carried by weight, size, and spacing.
- Division brand colors are fixed and must remain the accent identity per division.
- No professional photography or team logos are on hand yet for most teams (`media/logos` is currently empty) — design must hold up gracefully with missing team logos.

## Brand Commitments

- Existing mark: a geometric citrus-wedge symbol (`static/icons/CitrusLogo.png` / `CitrusLogoText.png`) used by the coach-portal (`CitrusApp`) login experience — light/white artwork meant for colored or dark backgrounds.
- Confirmed: the public league site should reuse the citrus-wedge motif as a recurring geometric device (not just as a static logo) to keep brand continuity between the coach portal and the public site.
- Confirmed tone: playful and energetic — personality and asymmetry are welcome — while still reading as a credible sports-league site with real standings and schedules.

## Evidence on Hand

- Real team names, live standings (via Citrus_api), and match schedules are already wired up and rendering in `LigueDesPamplemousseApp`.
- No team logos uploaded yet for most teams; no CA member photos yet; no league PDF documents uploaded yet. Design must handle these empty/missing-asset states without looking broken.

## Product Principles

1. The public site must always read as legitimate — real standings and schedules come first, personality is the seasoning, not the substance.
2. Division identity (color) should be felt everywhere a division is present, not just as a thin accent line.
3. Reuse and extend the citrus-wedge mark as a geometric system, not just a logo file.
4. Design for missing assets (no team logo, no photo, no documents yet) as a first-class state, not an afterthought.
5. French-first copy, Maven Pro-only typography, mobile-first.
