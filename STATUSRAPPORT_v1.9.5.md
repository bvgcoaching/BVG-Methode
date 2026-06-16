# STATUSRAPPORT v1.9.5 — Blessure-robuustheid + Optie A (coach-instructies)

**Datum:** 15 juni 2026 | **Engine:** v1.9.5 | **Bibliotheek:** v1.10 | **SOP:** v4.0

> Dit rapport consolideert taak F (FB-dagen lean) + de blessure-robuustheid. De repo stond op
> v1.9.3; alles hieronder komt daar bovenop in één upload.

## DEEL 1 — TAAK F: Full Body-dagen lean & professioneel (engine v1.9.4)
Owen's FB-dag was te lang (12 oef) en versnipperd. Vijf wijzigingen:
- **F1** (globaal, mannen): geen glute-fill meer (Billen uit FILL_POOLS); bilwerk via
  squat/hinge-spillover + 45° back extension. Owen: Billen 0.
- **F2** (globaal): schouders max 2 sets per oefening.
- **F3** (FB-dagen): overhead press toegestaan op FULL-dagtype (Upper blijft lateraal/achter).
- **F4** (FB-dagen): armen biceps 2 + triceps 2 op elke FB-dag.
- **F5** (FB-dagen): max 1 roterend accessoire per FB-dag (per cyclus+dagindex); prehab-slot
  van FB-dag af.
- **Bibliotheek v1.10:** Pols-contra toegevoegd aan 4 overhead presses (Romme's polsblessure
  kreeg anders een Seated DB Press).

## DEEL 2 — BLESSURE-ROBUUSTHEID (engine v1.9.5)

### Veiligheidsfix: synoniem-bewuste blessure-matching
**Probleem (gevonden bij grondige check):** blessure-invoer werd op exacte tokens gematcht.
Natuurlijke coach-tekst lekte: "knieblessure"/"knieën" lieten Barbell Back Squat + Leg Extension
door; "lage rug"/"rugpijn"/"lage rugklachten" lieten RDL + Back Squat door; "polsblessure",
"tenniselleboog", "schouderblessure" idem. Een coach die "lage rug" typt zou een klant een
deadlift geven — reëel blessurerisico.

**Opgelost:** `BLESSURE_SYNONIEMEN` (synoniem-map) + `actieve_blessure_contra()` met substring-
matching op de canonieke contra-indicaties (knie · schouder · onderrug · elleboog · pols). Alle
14 geteste varianten sluiten nu correct uit.

### Optie A: leesbare coach-instructies (geen globale blessure-veilig-vlag)
Sommige blessures sluiten ALLE oefeningen van een primaire spier uit (knie → alle 9 quads;
elleboog → alle 9 biceps). De engine programmeert die spier dan NIET en forceert nooit een
gecontra-indiceerde oefening. Nieuwe output-key **`coach_instructies`** geeft een leesbare
instructie: welke spier, welke blessure, "vul handmatig in met revalidatie-aanpak".

Voorbeeld (knieblessure): *"Quads: NIET automatisch geprogrammeerd — alle quads-oefeningen zijn
uitgesloten door de blessure (knie). Vul quads handmatig in met een revalidatie-aanpak die bij
deze specifieke blessure past; de engine forceert bewust geen gecontra-indiceerde oefening."*

**Bewust GEEN globale "blessure-veilig"-vlag op oefeningen.** Of een oefening veilig is hangt af
van de specifieke blessure (ACL ≠ patellapees ≠ meniscus). Een globale aanname zou élke
knie-geblesseerde klant dezelfde oefening geven — ook wie het schaadt. Dat blijft coach-oordeel
per klant. (Toekomst-optie: een per-klant `vrijgegeven_oefeningen`-veld in de intake; bewust niet
nu gebouwd.)

## VALIDATIE (volledige audit opnieuw, engine v1.9.5)
- 512-profielen-grid: 0 crashes, 0 invariant-schendingen.
- Volume consistent (0 mismatches/96), MEV-vloeren + 2×/week frequentie gehaald, 0 splinters.
- 13 adversariële inputs: 0 crashes.
- **Blessures:** 14 synoniem-varianten sluiten correct uit; geen lek bij enkele/combi/alle-5
  blessures; geen crash bij alle-5 + dislikes gestapeld.
- **Coach-instructies:** correct + leesbaar bij knie/elleboog/schouder; **0 valse positieven**
  bij 96 gezonde profielen.
- Owen/Romme/gezonde klant: FB-dagen lean, polsveilig, geen glute-fill voor mannen.

## OORDEEL
Engine v1.9.5 productie-klaar. Blessures worden robuust en veilig afgehandeld; de tool kent z'n
grenzen en is daar expliciet over richting de coach.

## AANDACHTSPUNTEN (geen bugs)
- `HERPLAATSING_RONDE_TEKORT`-flags: interne diagnostiek → filter uit klant-facing output.
- Core 2 sets/week (SOP-vloer) — bewuste keuze.
- Bestandsnaamgeving (versie-suffix → `(1)`/spatie-risico): overweeg vaste namen.

## OPEN (niet-engine / toekomst)
- Trainings-log / Supabase-koppeling (Owen eerst; HERPLAATSING-flags + coach_instructies netjes tonen).
- Per-klant `vrijgegeven_oefeningen`-veld (geblesseerde klant tóch volledig schema na coach-beoordeling).
