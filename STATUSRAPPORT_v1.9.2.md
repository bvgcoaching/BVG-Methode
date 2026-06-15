# STATUSRAPPORT v1.9.2 — Bil-selectie (meetfout, geen bug) + taak E (AF)

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

## TAAK E — ADDUCTOREN ALS EIGEN ACCESSOIRE-SPIERGROEP — ✅ AF (engine v1.9.2, bibliotheek v1.9)

**Besluit:** het binnenbeen (adductoren) moet een **eigen accessoire-spiergroep** worden — geen
biloefening, geen quad. "Het blijft een spier die op een gegeven moment getraind moet worden"
(Bas). Hip Adduction Machine staat NU voorlopig nog als `primaire_spier: Billen` met
`techniek_niveau: Gevorderd` (bibliotheek v1.8). Dat is NIET de eindstaat — het telt nu nog
onterecht als bilvolume voor gevorderden.

**GEÏMPLEMENTEERD (engine v1.9.2):**
1. ✅ Nieuwe spiergroep Adductoren met landmark `(0,2,2,4,6)`. NIET in focus-rotatie.
2. ✅ Ervaring-gated dosis: `ADDUCTOREN_VASTE_DOSIS = 2`, `ADDUCTOREN_MIN_ERVARING = (Gevorderd, Expert)`. Novice -> 0. Nieuw, herbruikbaar mechanisme.
3. ✅ `DAG_SPIEREN`: Adductoren toegevoegd aan FULL, LOWER, LEGS.
4. ✅ `verdeel_volume` kreeg `ervaring`-param + adductoren-dosis met gate.
5. ✅ `orden_sessie`: Adductoren als accessoire gecategoriseerd.
6. ✅ Bibliotheek v1.9: Hip Adduction Machine `Billen -> Adductoren`, notitie verwijderd. Billen nu 11 oefeningen (correct).

**GEVALIDEERD:**
- Gevorderde (3-5j): 2 adductoren-sets + Hip Adduction-oefening op Lower. ✓
- Novice (<1j): 0 adductoren, geen oefening, geen verdampend volume, geen rare flags. ✓
- Owen (beginner): weektotaal 79 ongewijzigd (geen regressie). ✓
- Vrouw bil-voorkeur gevorderd: billen 8 sets met échte bil-oefeningen; Hip Adduction nu correct als Adductoren (apart, niet meer in bil-telling). ✓
- Brede sweep: geen primaire spier onder MEV gedrukt door de adductoren-dosis. ✓

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
