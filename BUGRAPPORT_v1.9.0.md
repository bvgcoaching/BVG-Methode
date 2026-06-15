# BUGRAPPORT v1.9.0 — Bil-selectie knelt bij krappe profielen

**Datum:** 14 juni 2026
**Status:** open, te onderzoeken in volgende sessie
**Prioriteit:** middel (raakt alleen vrouw + bil-voorkeur bij krappe tijd; ruimere profielen werken)

---

## SAMENVATTING

Na taak A (vrouw-billen primair) krijgt Billen voor een vrouw met bil-voorkeur correct een
volume-doel toegewezen in `verdeel_volume()`. Maar bij **krappe profielen** (bv. 3 dagen /
75 min) plaatst de **selectie-motor er geen bil-oefeningen voor**: de eindoutput toont
`Billen=4` terwijl `verdeel_volume()` 8 teruggeeft, en de bil-oefening-lijst is leeg op elke dag.

Bij ruimere profielen (4 dagen, of 90 min) werkt het wél: Billen krijgt 9-13 sets met echte
oefeningen. De bug zit dus in de **interactie tussen volume-toewijzing en oefening-plaatsing
onder tijdsdruk**, niet in de landmark-wijziging zelf.

---

## REPRODUCTIE

```bash
cd /home/claude/BVG-Methode  # of waar de repo staat
# Testintake: vrouw, 3 dagen, 75 min, bil-voorkeur, INT
cat > /tmp/test_vrouw_bil.json << 'EOF'
{"naam":"Test Vrouw Bil","geslacht":"V","lichaamsgewicht":65,"dagen":3,"minuten":75,
"ervaring_bucket":"1-3","lifts":{"bench":35,"squat":70,"deadlift":85,"row":25},
"voorkeurspier":"Billen","dislikes":[],"blessures":[],"pijnlijke_oefeningen":[],
"materiaal_profiel":"commercieel","re_entry":false,"progressie_tracking":false}
EOF
python3 engine_v1.9.0.py --bibliotheek bibliotheek_v1.7.json --intake /tmp/test_vrouw_bil.json --cyclus 1
```

**Verwacht:** Billen ~7-8 sets, ingevuld met hip thrust / hip extension / etc.
**Werkelijk:** Billen=4, bil-oefening-lijst leeg per dag.

---

## WAT AL ONDERZOCHT IS (14 juni)

1. **`verdeel_volume()` werkt correct.** Directe aanroep met geslacht="V", voorkeur="Billen", INT:
   geeft `Billen=8` (MAV-laag 12 → met budget-knip naar 8). De vrouw-landmark
   `billen_landmark("V") = (4,8,12,16,20)` wordt correct gebruikt.

2. **`verdeel_over_dagen()` plaatst 7 van de 8.** Trace toonde:
   - LOWER: 5 bil-sets, FULL: 2 bil-sets, **onplaatsbaar: 3** (dagen zaten vol: LOWER 26/29,
     FULL 29/29). Dus hier verdampt al een deel — maar er komt nog 7 uit, niet 4.

3. **De eindpijplijn knipt verder naar 4.** Tussen `verdeel_over_dagen` (7) en de eindoutput (4)
   gebeurt iets in de selectie/herplaatsing. Flags bij dit profiel:
   `HERPLAATSING_RONDE_TEKORT_1/2/3/5`, `TIJDBUDGET_KNELT_ONDER_LANDMARK`.
   De bil-oefening-lijst is LEEG, dus de 4 sets die de output rapporteert komen waarschijnlijk
   via spillover-telling of fill, niet via geplaatste bil-oefeningen.

4. **Tegenstrijdigheid:** dagtotalen (Upper 27, Lower 22, Full 25) liggen ONDER de cap (29),
   tóch worden bil-oefeningen niet geplaatst en is er een TIJDBUDGET-knel-flag. Als er ruimte
   is op Lower (22<29), waarom plaatst de selectie-motor daar geen hip thrust? → kern van de bug.

---

## WAAR TE BEGINNEN (volgende sessie)

De bug zit in de **selectie-/plaatsingslaag**, niet in `verdeel_volume`. Kijk naar:

1. **`harde_filters(bib, spier, intake, eff_ervaring, cyclus)`** (rond regel 795) — worden
   bil-oefeningen onterecht weggefilterd? Check of de 11 bil-oefeningen door de materiaal- en
   techniek-filters komen voor dit profiel. Mogelijk worden ze gefilterd en blijft er volume
   zonder oefening over.

2. **De rondes-/herplaatsing-logica** (zoek `HERPLAATSING_RONDE_TEKORT`) — billen wordt
   toegewezen aan dagen maar de round-robin plaatsing krijgt de oefeningen er niet in. Waarom
   "tekort" terwijl er dag-ruimte is?

3. **Hypothese:** de `SESSIE_SPIER_CAP = 8` (max direct volume per spier per sessie) of de
   blokvolgorde-structuur (§8·V) duwt bil-oefeningen uit de rondes omdat billen laat in de
   prioriteit-volgorde staat en de grote compounds (quads/hams) de vroege slots claimen. Bij
   krappe tijd blijven er dan geen slots over voor billen, ook al is er nominaal cap-ruimte.

4. **Relatie met taak C:** dit raakt waarschijnlijk de dag-cap / herstel-plafond-interactie.
   Overweeg dit samen met taak C op te lossen (herstel-plafond kalibreren).

---

## TAAK C — STATUS NA ONDERZOEK 14 JUNI (belangrijke bevinding)

**Het oorspronkelijke taak-C-doel ("herstel-plafond 24/30/999 herijken") is ACHTERHAALD.**

Bij het inspecteren van engine v1.9.0 bleek dat het oude weektotaal-herstel-plafond
(24/30/999 per krachtniveau) **niet meer in de engine zit**. Het is in een eerdere
architectuurronde bewust vervangen door een ander model (zie engine-header regel 13-15):

- **Geen weektotaal-plafond meer.** In plaats daarvan reguleren de **per-spier RP-landmarks**
  het volume, begrensd door de **sessie-cap** (BASIS_CAP {45:15,60:21,75:27,90:32}) en de
  **per-spier junk-grens** (SESSIE_SPIER_CAP = 8 directe sets per spier per sessie).
- Verificatie: Owen (beginner, 3d/90min) produceert **79 directe sets/week**. Met een hard
  plafond van 24 was dat onmogelijk → plafond is aantoonbaar niet actief.
- De redenering achter de wijziging (engine-header): meer trainingsdagen verhogen hypertrofie
  nauwelijks bovenop het volume; de winst van extra dagen zit in **distributie binnen de
  per-sessie junk-grens**, niet in een hoger weektotaal. Daarom is het weektotaal-plafond
  vervangen door de per-sessie SESSIE_SPIER_CAP.

**Gevolg:** er valt aan "het herstel-plafond" niets te kalibreren — het bestaat niet meer als
los getal. Dit deel van taak C is daarmee afgehandeld (door eerdere architectuur, niet door
nieuw werk).

**Wat van taak C overblijft = ALLEEN de bil-selectie-bug hierboven.** Die is het echte,
concrete resterende werk. Mogelijk hangt de bug samen met SESSIE_SPIER_CAP of de blokvolgorde
(zie hypothese 3 hierboven). De spillover-verrekening in de bil-telling (squat/hinge meetellen)
blijft een los, kleiner taak-C-onderdeel dat pas zin heeft ná de selectie-bug.

---

## TAAK E — ADDUCTOREN ALS EIGEN ACCESSOIRE-SPIERGROEP (besluit Bas 14 juni, nog te bouwen)

**Besluit:** het binnenbeen (adductoren) moet een **eigen accessoire-spiergroep** worden — geen
biloefening, geen quad. "Het blijft een spier die op een gegeven moment getraind moet worden"
(Bas). Hip Adduction Machine staat NU voorlopig nog als `primaire_spier: Billen` met
`techniek_niveau: Gevorderd` (bibliotheek v1.8), maar dat is expliciet NIET de eindstaat — het
telt nu nog onterecht als bilvolume.

**Waarom nog niet gebouwd:** een nieuwe accessoire-spiergroep raakt de engine op ~6 plekken,
waaronder de **dag-plaatsingslaag (`verdeel_over_dagen`) — exact waar de bil-selectie-bug zit**.
Een nieuwe spiergroep door een buggy plaatsingslaag duwen = twee verstrengelde bugs. Daarom
samen met de bil-selectie-bug in één gerichte engine-sessie aanpakken. Besluit Bas: niet
tussendoor forceren.

**Checklist voor de bouw:**
1. `ACCESSOIRE_ROTATIE` of aparte accessoire-lijst — "Adductoren" toevoegen (hoeft niet per se in
   de focus-rotatie onderrug→houding→core→kuiten→billen→grip).
2. Accessoire-dosis bepalen — lage onderhoudsdosis (vgl. Kuiten 4 / Core 3 / Onderrug 3),
   **ALLEEN Gevorderd/Expert** (Novice = 0). Mechanisme voor ervaring-afhankelijke accessoire-
   dosis bestaat nog niet → ontwerpen.
3. `DAG_SPIEREN` — Adductoren toevoegen aan LOWER, LEGS, FULL.
4. `verdeel_volume` accessoire-loop — nieuwe categorie + ervaring-gating.
5. `verdeel_over_dagen` — plaatsing (raakt de bil-selectie-bug; samen oplossen).
6. `FILL_WEEK_CAP` — eventueel een cap voor Adductoren.
7. Bibliotheek: Hip Adduction Machine `primaire_spier: Billen -> Adductoren`, `_notitie_taakD`
   verwijderen. Eventueel meer adductoren-oefeningen (nu maar 1).
8. SOP: §4 (accessoire-laag) + §5 bijwerken.

**Resultaat na taak E:** adductoren is een volwaardige (kleine) accessoire-spier die voor
gevorderden een onderhoudsdosis krijgt op been-dagen, los van de bil-telling.

---

## BELANGRIJK — NIET DOEN

- **Geen A3-herverdeling bouwen.** Besluit Bas 14 juni: bil-voorkeur verdringt quads/hams NIET
  actief; de dag-cap + spillover bepalen de balans. Voor een vrouw met bil-voorkeur geeft de
  engine bij werkbare profielen ~10 effectieve bil-sets (7 direct + 3 spillover), ruim in de
  MAV-zone. Dat is de gewenste uitkomst. De bug is dat KRAPPE profielen zelfs die 7 niet halen
  in de selectie — dát moet gefixt, niet het volume verder opdrijven.
