# STATUSRAPPORT v1.9.3 — Grondige audit + 2 bugfixes

**Datum:** 15 juni 2026
**Engine:** v1.9.3 | **Bibliotheek:** v1.9 | **SOP:** v3.8
**Aanleiding:** Bas vroeg om een grondige check of de engine volledig functioneel is en een
professioneel resultaat oplevert vóór inzet bij echte klanten.

---

## SAMENVATTING / OORDEEL

De engine is grondig geauditeerd over **honderden profielen** met harde invariant-checks plus
adversariële input. Er zijn **twee echte bugs gevonden en gefixt**. Na de fixes:

- **512-profielen-grid** (M/V × 2-5 dagen × 45-90 min × 4 ervaringsniveaus × 2 krachtniveaus ×
  wel/geen voorkeur): **0 crashes, 0 invariant-schendingen.**
- **Gerapporteerd volume == geplaatst volume**: 0 mismatches (was 111).
- **Geen 1-set splinters**: 0 (was 4).
- **MEV-vloeren** gehaald bij ruime tijd (90min, 4-5d): alle primaire spieren.
- **2x/week frequentie** gehaald bij ruime tijd.
- **Techniek-gating**: geen oefening boven ervaringsniveau.
- **Dislikes/pijnlijke oefeningen**: correct uitgesloten.
- **Re-entry overlay**: draait, capt pool, vlagt correct.
- **13 adversariële inputs** (lege lifts, 1/6/7 dagen, niet-standaard minuten, onzin-voorkeur,
  onzin-ervaring, álle compounds disliked, lichaamsgewicht 0, ontbrekende velden): **0 crashes**,
  allemaal valide output met flags.

**Oordeel: de engine is productie-klaar voor schemageneratie.** De gegenereerde schema's lezen
als professionele programma's (correcte blokvolgorde, push-pull interleave, rep-ranges, rust,
guardrails, bil-prioriteit voor vrouwen, adductoren voor gevorderden).

---

## BUG 1 (KRITISCH) — volume_per_spier klopte niet met het schema

**Symptoom:** `volume_per_spier` rapporteerde een ander aantal sets dan er werkelijk in het
schema stonden. 111 mismatches over 96 profielen. Bijv. Schouders gerapporteerd 7, geplaatst 8.

**Oorzaak:** het getal werd berekend uit het pre-plaatsings-plan (`per_dag`), niet uit het
werkelijke schema. Twee bronnen van afwijking: (a) prehab-sets (bv. rear-delt fly = schouder)
werden niet meegeteld; (b) afronding bij het splitsen van weekvolume in hele oefeningen.

**Fix:** `volume_per_spier` wordt nu berekend door de daadwerkelijk geplaatste sets in
`basisweek` te tellen. De samenvatting klopt nu per definitie met wat de klant in zijn schema
ziet — inclusief prehab en afronding. (Dit is exact de soort rapportage-inconsistentie die een
tool onprofessioneel maakt; vandaar kritisch.)

## BUG 2 (KLEIN) — 1-set splinters bij krappe sessietijd

**Symptoom:** bij 45-min-sessies kreeg soms één spier 1 set op een dag (bv. Borst 1× op Upper 1).
SOP-regel: min-2-vloer, nooit 1-set splinters. 4 gevallen.

**Oorzaak:** in `verdeel_over_dagen` (freq=2-tak) eiste de cap-check dat de SOM van de dagruimte
op twee dagen ≥4 was, maar niet dat ELKE dag ≥2 ruimte had. Bij krappe cap kon één dag 1 ruimte
hebben → 1-set splinter.

**Fix:** freq=2 alleen als beide gekozen dagen ≥2 ruimte hebben; anders terugval op 1 dag (SOP).
Plus een vangnet in de plaatsing (`plaatsbaar < 2 → 0`).

---

## AANDACHTSPUNTEN (geen bugs — voor later / presentatie)

1. **`HERPLAATSING_RONDE_TEKORT_<n>`-flags** verschijnen vaak in de output. Dit zijn interne
   diagnostiek-vlaggen van de ordeningslaag; ze duiden GEEN kapot schema aan (geverifieerd:
   geen ontbrekende spieren, geen dubbele oefeningen, alles compleet). **Aanbeveling:** filter
   deze uit de klant-facing output bij de log/dashboard-koppeling. Coach/systeem-diagnostiek,
   niet voor de klant.

2. **Core staat op 2 sets/week** (de harde vloer) — voor gevorderden aan de lage kant. Bewuste
   SOP-ontwerpkeuze (core = accessoire + indirect werk). Overweeg of dit zo moet blijven.

3. **Naamgeving bestanden** (eerder geparkeerd): de versie-suffixen in bestandsnamen veroorzaken
   `(1)`/spatie-problemen bij her-upload. Overweeg vaste namen (`bvg_engine.py` etc.) met de
   versie alleen ín het bestand + git-historie.

---

## OPEN (niet-engine)

- **Trainings-log / Supabase-koppeling**: engine-output wegschrijven zodat klanten het in de PWA
  zien. Owen eerst. Volgende fase.
- **Optionele verfijning**: spillover-verrekening expliciet in de bil-telling (klein, laag-prio).

Geen openstaande engine-bugs.
