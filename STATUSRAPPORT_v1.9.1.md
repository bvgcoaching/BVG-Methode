# STATUSRAPPORT v1.9.1 — Bil-selectie (OPGELOST: bug bestond niet) + taak E

**Datum:** 14 juni 2026
**Status:** de eerder gerapporteerde "bil-selectie-bug" was een MEETFOUT, geen echte bug.

---

## DE "BIL-SELECTIE-BUG" BESTOND NIET — MEETFOUT IN DE DIAGNOSE

**Eerder gerapporteerd (fout):** "Bij krappe profielen krijgt Billen wel volume maar plaatst
de selectie-motor geen bil-oefeningen; de bil-oefening-lijst is leeg per dag."

**Werkelijkheid:** de engine plaatst bil-oefeningen correct, op alle geteste profielen. De
foutieve conclusie kwam doordat het diagnose-script de output filterde op het veld
`primaire_spier`, terwijl de output-regels het veld **`spier`** gebruiken (zie assemblage in
`genereer`: `"spier": o.get("primaire_spier")`). Filteren op de verkeerde key gaf telkens een
lege lijst → de valse conclusie "geen bil-oefeningen".

**Verificatie (engine v1.9.1 + bibliotheek v1.8), filterend op de JUISTE key `spier`:**
- 3 dagen / 75 min: Billen 4 sets — 45 Hip Extension (bil-focus) + 1 biloefening op FB. ✓
- 3 dagen / 90 min: Billen 9 sets — 45 Hip Extension + Hip Abduction + Cable Box Step-up +
  Machine Hip Thrust. ✓
- 4 dagen / 75 min: Billen 13 sets — vier bil-oefeningen over twee Lower-dagen. ✓

**Les:** controleer altijd de output-key voordat je een afwezigheid als bug bestempelt. De
keten verdeel_volume → verdeel_over_dagen → harde_filters → kies_oefening → orden_sessie →
assemblage werkt voor billen end-to-end. Dit is stap voor stap getraceerd en bevestigd.

---

## WAT WÉL WAAR IS (normaal gedrag, geen bug)

Bij het KRAPSTE profiel (3d/75min) krijgt billen 4 directe sets terwijl `verdeel_volume` er 8
toewijst. Dat verlies is **normaal capaciteit-gedrag**, geen fout: de been-/FB-dagen zitten vol
(dag-cap), dus niet al het toegewezen bilvolume past als directe sets. Met squat/hinge-spillover
(~3 effectief) erbij zit billen alsnog rond ~7 effectieve sets — ruim boven MEV. Dit is precies
de uitkomst die Bas 14 juni akkoord vond (dag-cap + spillover bepalen de balans, geen actieve
verdringing van quads/hams). GEEN actie nodig.

---

## TAAK E — ADDUCTOREN ALS EIGEN ACCESSOIRE-SPIERGROEP (besluit Bas 14 juni, nog te bouwen)

**Besluit:** het binnenbeen (adductoren) moet een **eigen accessoire-spiergroep** worden — geen
biloefening, geen quad. "Het blijft een spier die op een gegeven moment getraind moet worden"
(Bas). Hip Adduction Machine staat NU voorlopig nog als `primaire_spier: Billen` met
`techniek_niveau: Gevorderd` (bibliotheek v1.8). Dat is NIET de eindstaat — het telt nu nog
onterecht als bilvolume voor gevorderden.

**Checklist voor de bouw:**
1. `ACCESSOIRE_ROTATIE` of aparte accessoire-lijst — "Adductoren" toevoegen (hoeft niet per se in
   de focus-rotatie onderrug→houding→core→kuiten→billen→grip).
2. Accessoire-dosis bepalen — lage onderhoudsdosis (vgl. Kuiten 4 / Core 3 / Onderrug 3),
   **ALLEEN Gevorderd/Expert** (Novice = 0). Mechanisme voor ervaring-afhankelijke accessoire-
   dosis bestaat nog niet → ontwerpen.
3. `DAG_SPIEREN` — Adductoren toevoegen aan LOWER, LEGS, FULL.
4. `verdeel_volume` accessoire-loop — nieuwe categorie + ervaring-gating.
5. `verdeel_over_dagen` — plaatsing controleren.
6. `FILL_WEEK_CAP` — eventueel een cap voor Adductoren.
7. Bibliotheek: Hip Adduction Machine `primaire_spier: Billen -> Adductoren`, `_notitie_taakD`
   verwijderen. Eventueel meer adductoren-oefeningen (nu maar 1).
8. SOP: §4 (accessoire-laag) + §5 bijwerken.

**Resultaat na taak E:** adductoren is een volwaardige (kleine) accessoire-spier die voor
gevorderden een onderhoudsdosis krijgt op been-dagen, los van de bil-telling.

---

## OVERIGE OPEN PUNTEN

- **Taak C — herstel-plafond:** OPGEHELDERD (bestaat niet meer in de engine; vervangen door
  landmark + sessie-cap + SESSIE_SPIER_CAP=8). Niets te kalibreren.
- **Optionele verfijning:** spillover-verrekening expliciet meetellen in de bil-telling. Klein,
  laag-prioriteit; de huidige conservatieve aanpak (spillover als "gratis extra") werkt prima.

## BELANGRIJK — NIET DOEN

- **Geen A3-herverdeling bouwen.** Besluit Bas 14 juni: bil-voorkeur verdringt quads/hams NIET
  actief; dag-cap + spillover bepalen de balans. Bij werkbare profielen ~10 effectieve bil-sets.
  Dat is de gewenste uitkomst.
