#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BVG METHODE - SELECTIE-ENGINE  ·  v1.4 (per-spier MEV/MRV-landmarks; volledig getest)
Port van SOP v3.2: B1 (incl. re-entry), C1 (cap + herstel-plafond), C2 (twee lagen),
B3 (voorkeurspier), cyclusstructuur, B5 (selectie-motor, 7 lagen), B6/B7 (interim).

================================ WAARSCHUWING =================================
1. v1.2 (10 juni 2026): VOLLEDIGE pijplijn getest tegen bibliotheek v1.4 (108
   oefeningen) en gediffd tegen de referentie-schema's van Romme en Owen.
   v1.4 (11 juni): C2 herzien naar per-spier volumelandmarks (Renaissance
   Periodization MEV->MRV), geschaald op krachtniveau. Vervangt het weektotaal-
   plafond. Reden: frequentie verhoogt hypertrofie nauwelijks bovenop volume
   (Pelland et al. 2025); winst van meer dagen = distributie binnen de per-sessie
   junk-grens (SESSIE_SPIER_CAP), niet een hoger weektotaal-plafond. Besluiten Bas:
   armen hard direct-doel 4 (stubborn-muscle, beschermd tegen tijd-/cap-knip),
   billen accessoire-MEV bij man, voorkeur-lean +2, tijd-budget = secundaire
   begrenzer (schema MOET in opgegeven tijd passen).
2. Gesourcde waarden (krachtdrempels m/v + Epley, week-fasen, B6-tabellen) zijn
   verbatim gemerged uit SOP v3.2. Constantes met "INTERIM_OPEN" wachten op een
   besluit van Bas (herstel-plafond, vrouw-cap, re-entry-band); "INTERIM_ONGEVERIFIEERD"
   wacht op de bibliotheek v1.4 (big-three-namen, materiaal-tags).
3. Tag-waarden (patroon/materiaal) worden tolerant gematcht (substring,
   lowercase). Bij de eerste testrun verifieren tegen de echte bibliotheek.
===============================================================================

GEBRUIK
    python bvg_engine.py --bibliotheek bib_v1_4.json --intake intake.json --cyclus 1

INTAKE-JSON (verwacht)
{
  "naam": "Romme Gudde", "geslacht": "M", "lichaamsgewicht": 90,
  "dagen": 2, "minuten": 75,
  "ervaring_bucket": "1-3",
  "lifts": {"bench": 70, "squat": 90, "deadlift": 110, "row": 30},
  "voorkeurspier": "Borst",
  "dislikes": [], "blessures": ["pols"], "pijnlijke_oefeningen": ["Overhead Press"],
  "materiaal_profiel": "commercieel",
  "re_entry": true, "progressie_tracking": false
}
"""

import argparse
import hashlib
import json
import sys
from collections import defaultdict

# v1.8.3 (12 juni 2026): volgorde-laag vervangen door SOP v3.3 par.8-V —
# rondes (round-robin), opener-rotatie per cyclus (c1 rug / c2 borst, alleen
# zonder voorkeurspier), slot-3-guardrail voor squat/hinge op FULL/LOWER,
# HARDE synergist-bescherming (geen arm-isolatie voor de laatste relevante
# compound), isolatie-only spiergroepen na het compound-werk. Accessoires
# (kuiten/onderrug/prehab) blijven na het hoofdwerk, core blijft laatst.
ENGINE_VERSIE = "1.9.6-canonieke-taxonomie"

# ═══════════════════════════════════════════════════════════════════════════
# v1.9.6 (2 juli 2026): CANONIEKE SPIER-TAXONOMIE OP DE OUTPUT.
# De database (Supabase `oefeningen` + alle klant_schemas) is genormaliseerd naar
# 13 canonieke waarden, incl. gesplitste deltakoppen. De bibliotheek kan nog oude
# varianten bevatten (Bicep/Biceps, Hams/Hamstring, Schouder Zij/Rear Delt, ...).
# Deze laag normaliseert ALLES wat de engine uitstoot, zodat vieze bibliotheek-
# waarden nooit meer de database in lekken. De interne motor (RP_LANDMARKS met
# samengevoegde "Schouders"/"Quads"/"Hams") blijft ongemoeid — dit raakt alleen
# de output. Validatie in main() faalt hard op onbekende waarden.
# ═══════════════════════════════════════════════════════════════════════════
SPIER_CANONIEK = frozenset([
    "Borst", "Rug", "Biceps", "Triceps", "Quadriceps", "Hamstrings",
    "Kuiten", "Core", "Onderrug", "Adductoren",
    "Schouder Voor", "Schouder Zij", "Schouder Achter",
    "Billen",  # nog niet in het DB-register; gereserveerd voor glute-oefeningen
])

# Per-oefening overrides: de deltakop hangt van de oefening af, niet van het label.
_SPIER_PER_OEFENING = {
    "cable lateral raise": "Schouder Zij",
    "single arm cable lateral raise": "Schouder Zij",
    "dumbbell lateral raise": "Schouder Zij",
    "machine lateral raise": "Schouder Zij",
    "face pull": "Schouder Achter",
    "reverse pec deck": "Schouder Achter",
    "chest-supported reverse fly": "Schouder Achter",
    "single-arm cable rear delt fly": "Schouder Achter",
    "seated dumbbell press": "Schouder Voor",
    "machine shoulder press": "Schouder Voor",
    "overhead barbell press": "Schouder Voor",
    "smith shoulder press": "Schouder Voor",
}

# Waarde-remaps: alle bekende varianten -> canoniek.
_SPIER_REMAP = {
    "bicep": "Biceps", "biceps": "Biceps",
    "tricep": "Triceps", "triceps": "Triceps",
    "quad": "Quadriceps", "quads": "Quadriceps", "quadriceps": "Quadriceps",
    "hams": "Hamstrings", "hamstring": "Hamstrings", "hamstrings": "Hamstrings",
    "kuit": "Kuiten", "kuiten": "Kuiten",
    "adductor": "Adductoren", "adductoren": "Adductoren",
    "billen": "Billen", "glutes": "Billen", "glute": "Billen",
    "rear delt": "Schouder Achter", "schouder achter": "Schouder Achter",
    "schouder zij": "Schouder Zij", "schouder voor": "Schouder Voor",
    "borst": "Borst", "rug": "Rug", "core": "Core", "onderrug": "Onderrug",
    "lower back": "Onderrug",
}

def normaliseer_spier(oef_naam, spier):
    """Canonieke spierwaarde voor de output. Oefening-specifieke deltakop-override
    eerst, dan waarde-remap. 'Schouder'/'Schouders' zonder kop-info valt terug op
    'Schouder Zij' (engine programmeert laterals als schouder-default, zie F3)."""
    naam_lc = str(oef_naam or "").strip().lower()
    if naam_lc in _SPIER_PER_OEFENING:
        return _SPIER_PER_OEFENING[naam_lc]
    s_lc = str(spier or "").strip().lower()
    if s_lc in _SPIER_REMAP:
        return _SPIER_REMAP[s_lc]
    if s_lc in ("schouder", "schouders"):
        if any(t in naam_lc for t in ("press", "ohp", "overhead")):
            return "Schouder Voor"
        if any(t in naam_lc for t in ("rear", "reverse", "face pull")):
            return "Schouder Achter"
        return "Schouder Zij"
    return str(spier or "").strip()

def valideer_taxonomie(resultaat):
    """Controleer dat elke uitgestoten spierwaarde canoniek is. Retourneert lijst fouten."""
    fouten = []
    for sessie in resultaat.get("basisweek", []):
        for regel in sessie.get("oefeningen", []):
            if regel.get("spier") not in SPIER_CANONIEK:
                fouten.append("%s -> '%s' is niet canoniek" % (regel.get("oefening"), regel.get("spier")))
    return fouten
# v1.9.5 (15 juni 2026, blessure-robuustheid + Optie A):
#   SAFETY: blessure-invoer is nu synoniem-bewust (substring-match). Exacte-token-match liet
#     varianten lekken ("knieblessure"/"lage rug"/"rugpijn"/"polsblessure"/"tenniselleboog").
#     Nu via BLESSURE_SYNONIEMEN + actieve_blessure_contra(): "lage rugklachten"->onderrug enz.
#   OPTIE A: nieuwe output-key "coach_instructies" — leesbare instructie wanneer een PRIMAIRE
#     spier niet (veilig) geprogrammeerd kon worden (bv. knie sluit alle quads uit). De engine
#     forceert NOOIT een gecontra-indiceerde oefening; benoemt de blessure + wat de coach moet
#     doen. Geen globale "blessure-veilig"-vlag (te gevaarlijk; blijft coach-oordeel per klant).
#   Geaudit: 512-grid 0 crashes/0 schendingen; 0 valse coach-instructies bij gezonde klanten;
#   14 blessure-synoniemen sluiten correct uit; geen lek bij enkele/combi/alle-5 blessures.
# v1.9.4 (15 juni 2026, taak F — Full Body-dagen lean & professioneel maken):
#   F1: mannen geen glute-fill meer (Billen uit FILL_POOLS); bilwerk via spillover + 45 back ext.
#   F2: schouders max 2 sets per oefening (chunks van 2, geen splinter).
#   F3: op FULL-dagen mag schouder een overhead press zijn (Upper blijft lateraal/achter);
#       pols/schouder-blessure sluit press uit via contra-indicatie (bibliotheek v1.10).
#   F4: armen (bi 2 + tri 2) op ELKE FB-dag.
#   F5: max 1 roterend accessoire per FB-dag (per cyclus+dagindex); prehab-slot van FB-dag af.
#   Nieuw: normaliseer_fb_dagen(). Geaudit: 512-grid 0 crashes/0 schendingen, volume consistent,
#   MEV+frequentie gehaald, 13 adversariële inputs 0 crashes. Owen/Romme/gezond gevalideerd.
# v1.9.3 (15 juni 2026, grondige audit Bas+Claude — 2 bugs gevonden & gefixt):
#   FIX 1 (volume-rapportage): volume_per_spier werd berekend uit het pre-plaatsings-plan
#     (per_dag) i.p.v. het werkelijke schema. Verschil door prehab-sets (niet meegeteld) +
#     afronding bij oefening-splitsing. Gaf 111 mismatches over 96 profielen. Nu berekend uit
#     de daadwerkelijk geplaatste sets in basisweek -> samenvatting klopt altijd met schema.
#   FIX 2 (1-set splinters): verdeel_over_dagen kon bij krappe cap (45min) een 1-set splinter
#     plaatsen omdat de cap-check alleen de SOM van dagruimte >=4 eiste, niet >=2 per dag.
#     Nu: freq=2 alleen als ELKE dag >=2 ruimte heeft, anders terugval op 1 dag (SOP min-2-vloer).
#     + vangnet in plaatsing. Gaf 4 splinters; nu 0.
#   GEAUDIT: 512-profielen-grid (0 crashes, 0 invariant-schendingen), MEV-vloeren gehaald bij
#     ruime tijd, 2x/week frequentie gehaald, 13 adversariële inputs (lege lifts, 1/6/7 dagen,
#     onzin-waarden, alle-compounds-disliked, lichaamsgewicht 0, ontbrekende velden) = 0 crashes.
# v1.9.1 (14 juni 2026, taak D-deel): kies_oefening tier() kent nu "vermijden":
#   coach_prioriteit "vermijden" -> tier 9 (laatste redmiddel, alleen als er niets
#   anders in de pool zit). Gebruikt voor Sumo Deadlift (besluit Bas: bijna nooit zien).
# v1.9.0 (14 juni 2026, Bas + Claude):
#   TAAK B: VROUW_CAP_BONUS 1 -> 2 (vrouwen herstellen sneller tussen sets; sessie-cap,
#           niet weektotaal). Geverifieerd: cap 28->29 (75min), bilvolume in verdeel_volume
#           5->8 bij vrouw-bil-voorkeur.
#   TAAK A: Billen is voor VROUWEN een hoofdspier (laag-1) met eigen landmarks
#           RP_LANDMARKS_BILLEN_VROUW = (4,8,12,16,20), via billen_landmark(geslacht).
#           verdeel_volume() kreeg geslacht-param; Billen wordt voor vrouwen niet meer als
#           accessoire geroteerd maar als primaire spier behandeld (3 plekken aangepast).
#           Geverifieerd: geen regressie voor mannen (output identiek). Vrouw-bilvolume
#           schaalt mooi bij ruimere profielen (4d -> 13 sets).
#   BEKENDE BUG (zie BUGRAPPORT_v1.9.0.md): bij KRAPPE profielen (3d/75min) krijgt Billen
#           wel volume toegewezen (verdeel_volume=8) maar de SELECTIE-MOTOR plaatst er geen
#           bil-OEFENINGEN voor (eindoutput Billen=4, bil-oef-lijst leeg per dag, flags
#           HERPLAATSING_RONDE_TEKORT). Volume-laag werkt; selectie/plaatsing-laag knelt.
#           Apart van de landmark-wijziging. Te onderzoeken: harde_filters + rondes-logica.
#   NOG OPEN: taak C (herstel-plafond kalibreren + dag-cap-interactie), taak D (ladder-review
#           + Hip Adduction her-tag). A3-herverdeling BEWUST NIET gebouwd (besluit Bas 14/6:
#           dag-cap + spillover bepalen de balans, geen actieve verdringing quads/hams).

# ----------------------------- SOP-CONSTANTEN (vastgesteld) -----------------

PRIMAIR = ["Borst", "Rug", "Schouders", "Biceps", "Triceps", "Quads", "Hams", "Billen"]
ACCESSOIRE_SPIEREN = ("Kuiten", "Core", "Onderrug")  # laag-2-spieren (landmark-gestuurd)

# BESLUIT 11 juni #5 (Bas): billen = accessoire (man), en ALLE accessoires roteren in
# nadruk over cycli — elke cyclus krijgt EEN accessoire de focus (volume naar MAV-laag),
# de rest draait op baseline (MEV). Core heeft een hard weekminimum: komt ALTIJD elke
# week voor, en gaat bij tijdsdruk naar minimaal voordat een primaire spier sneuvelt.
ACCESSOIRE_ROTATIE = ("Billen", "Kuiten", "Core", "Onderrug")
CORE_WEEK_MINIMUM = 2  # harde ondergrens, nooit 0

# BESLUIT 11 juni #6 (Bas): de cyclusfocus is COACH-LOGICA, geen willekeurige rotatie.
# Kandidaten: houding/rear-delt en grip (via het prehab-slot + selectie) en de vier
# accessoire-spieren (via de MAV-laag-volume-bump). De volgorde volgt uit:
#  1. SYNERGIE met de voorkeurspier (veel persen -> achterkant schouder/houding;
#     zwaar trekken -> core stabiliseert; squat/hinge-prioriteit -> onderrug/core).
#  2. ANTICIPATIE: re-entry cyclus 2 opent zwaarder vrij/hinge-werk -> onderrug
#     staat dan op positie 2 ("de cyclus zelf of de cyclus ervoor", besluit Bas).
#  3. AFWISSELING: elke kandidaat komt precies 1x per ronde aan bod, daarna herhaalt
#     de logische volgorde. Tie-break = vaste rang (houding>core>onderrug>kuiten>billen>grip).
FOCUS_KANDIDATEN = ("houding", "core", "onderrug", "kuiten", "billen", "grip")
# BESLUIT 12 juni (Bas): VASTE focus-rotatie i.p.v. synergie-weging. Logische,
# voorspelbare aflopende volgorde voor iedereen — beschermend/fundamenteel eerst
# (onderrug=fundament onder hinge/squat, houding=schoudergezondheid tegen perswerk,
# core=rompstabiliteit), aesthetisch/ondersteunend later (kuiten=verwaarloosd,
# billen=heupkracht, grip=onderarm). De voorkeurspier-focus wordt overgeslagen.
FOCUS_ROTATIE_VAST = ["onderrug", "houding", "core", "kuiten", "billen", "grip"]
FOCUS_SYNERGIE = {  # GEDEPRECEerd 12 juni (vervangen door FOCUS_ROTATIE_VAST) — bewaard ter referentie
    "Borst":     {"houding": 3, "core": 1},
    "Schouders": {"houding": 3, "core": 1},
    "Rug":       {"core": 2, "grip": -1},
    "Quads":     {"core": 2, "onderrug": 2},
    "Hams":      {"onderrug": 3, "core": 1},
    "Billen":    {"onderrug": 2, "core": 1},
}
FOCUS_SPIER = {"core": "Core", "onderrug": "Onderrug",
               "kuiten": "Kuiten", "billen": "Billen"}


def focus_sequentie(voorkeur, re_entry):
    """VASTE accessoire-focus-rotatie (BESLUIT 12 juni, Bas): iedereen loopt
    dezelfde logische volgorde af i.p.v. een per-klant synergie-weging — dat is
    voorspelbaar en uitlegbaar voor klant en coach. Volgorde = beschermend/
    fundamenteel eerst (onderrug, houding, core), aesthetisch/ondersteunend later
    (kuiten, billen, grip). De focus die de VOORKEURSPIER dupliceert wordt
    overgeslagen (die krijgt al directe prioriteit via de voorkeur-route)."""
    seq = [k for k in FOCUS_ROTATIE_VAST if FOCUS_SPIER.get(k) != voorkeur]
    return seq or list(FOCUS_ROTATIE_VAST)


def focus_rationale(focus, voorkeur, re_entry, cyclus):
    """Klantgerichte uitleg die op het schema komt — de klant moet ZIEN dat dit
    voor hem is ontworpen (retentie via zichtbare personalisatie)."""
    if focus == "houding":
        basis = "Extra aandacht voor de achterkant van je schouders en je houding"
        if voorkeur in ("Borst", "Schouders"):
            return (basis + f" — met jouw {voorkeur.lower()}-prioriteit zit er veel "
                    "perswerk in je programma; dit houdt je schouders gezond en je "
                    "houding sterk, zodat je kunt blijven persen.")
        return basis + " — sterke achterkant = gezonde schouders en een rechte rug."
    if focus == "onderrug":
        if re_entry and cyclus == 2:
            return ("Deze cyclus bouwen we je onderrug gericht op — de komende "
                    "periode wordt het hinge- en vrije-stang-werk zwaarder, en een "
                    "sterke onderrug draagt dat.")
        if voorkeur in ("Hams", "Billen", "Quads"):
            return ("Focus op je onderrug — die ondersteunt direct je zware "
                    "onderlichaam-werk en maakt je hinges sterker.")
        return "Focus op je onderrug — het fundament onder al je zware oefeningen."
    if focus == "core":
        if voorkeur == "Rug":
            return ("Focus op je core — een sterke romp stabiliseert je zware "
                    "roeibewegingen en til-werk, precies waar jouw prioriteit ligt.")
        return ("Focus op je core — een sterke romp draagt al je grote oefeningen "
                "en je houding door de werkdag.")
    if focus == "kuiten":
        return ("Deze cyclus krijgen je kuiten de focus — kuiten reageren op "
                "consistente, gerichte aandacht en vallen anders snel tussen wal en schip.")
    if focus == "billen":
        return ("Extra bilwerk deze cyclus — heupkracht geeft balans in je "
                "onderlichaam en ondersteunt je squat- en hinge-patronen.")
    if focus == "grip":
        return ("Gripfocus — sterkere handen en onderarmen tillen letterlijk je "
                "hele training omhoog.")
    return ""


SPILLOVER = {"Borst": 0.0, "Rug": 0.0, "Schouders": 3.0, "Biceps": 5.5,
             "Triceps": 5.5, "Quads": 1.0, "Hams": 1.5, "Billen": 3.0}
# BESLUIT 11 juni #1 (Bas): stubborn-muscle hard direct-doel — armen krijgen altijd
# degelijk direct werk, los van spillover-rekenwerk. Matcht beide referentie-schema's
# en de stubborn-muscle-regel (RP: bi/tri MEV ~6, maar BVG-praktijk = 4 direct als floor).
DIRECT_DOEL_HARD = {"Biceps": 4, "Triceps": 4}
# BESLUIT 11 juni #2 (Bas): billen bij een man = accessoire-prioriteit, niet zo zwaar
# als hams. MEV-doel laag, leunt verder op hinge/squat-spillover. (Bij vrouw via
# voorkeurmechanisme op te schroeven — SOP par.11.)
SPILLOVER_KWALITEIT = {"Biceps": 0.5, "Triceps": 1.0, "Schouders": 0.7,
                       "Quads": 1.0, "Hams": 1.0, "Billen": 1.0}

BASIS_CAP = {45: 15, 60: 21, 75: 27, 90: 32}               # SOP par.3
BIG3_STRAF = 3
UNILATERAAL_TIJD = 1.5                                     # SOP par.8
CYCLUS_WEKEN = {"BEG": 8, "INT": 6, "ADV": 5}              # SOP par.6
ERVARING_RANG = {"Novice": 0, "Gevorderd": 1, "Expert": 2}
ERVARING_UIT_BUCKET = {"<1": "Novice", "1-3": "Gevorderd",
                       "3-5": "Gevorderd", "5+": "Expert"}

# ------------------- OPEN/ONGEVERIFIEERDE CONSTANTEN (zie header) -----------

# DEFINITIEF (SOP v3.2 par.1, verbatim uit SOP v1 B1; overhaul: "tabellen ongewijzigd"):
# drempels gelden op GESCHATTE 1RM / lichaamsgewicht — niet op rauw werkgewicht.
KRACHTDREMPELS = {
    "man":   {"bench": (1.00, 1.50), "squat": (1.50, 2.00),
              "deadlift": (2.00, 2.50), "row": (0.75, 1.10)},
    "vrouw": {"bench": (0.60, 0.90), "squat": (1.20, 1.60),
              "deadlift": (1.60, 2.00)},  # row: geen drempel (optioneel signaal)
}
SBD = ("bench", "squat", "deadlift")  # mediaan over SBD; row = bonussignaal


def schat_1rm(kg, reps, flags):
    """SOP v3.2 par.1-1RM: Epley (reps<=8) / gemiddeld Epley+Brzycki (9-12) / Epley+flag (>12)."""
    kg = float(kg); reps = int(reps)
    epley = kg * (1 + reps / 30.0)
    if reps <= 8:
        return epley
    brzycki = kg * 36.0 / (37.0 - reps) if reps < 37 else epley
    if reps <= 12:
        return (epley + brzycki) / 2.0
    flags.append("HIGH_REPS_UNRELIABLE_1RM")
    return epley

# BESLUITEN 11 juni 2026 (Bas, chat) — C2 herzien naar per-spier volumelandmarks.
# Reden: frequentie verhoogt hypertrofie nauwelijks bovenop volume (Pelland et al. 2025);
# de winst van meer dagen is distributie binnen de per-sessie junk-grens, niet een hoger
# weektotaal-plafond. De echte bovengrens is PER SPIER (MEV->MRV), niet als weektotaal.
#
# Volumelandmarks per spier (wekelijkse harde sets) — Renaissance Periodization (Israetel),
# geverifieerd via mesostrength.com 11 juni 2026. (MV, MEV, MAV-laag, MAV-hoog, MRV).
RP_LANDMARKS = {
    "Borst":     (8, 10, 12, 20, 22),
    "Rug":       (8, 10, 14, 22, 25),
    "Quads":     (6, 8,  12, 18, 20),
    "Hams":      (4, 6,  10, 16, 20),
    "Schouders": (6, 8,  16, 22, 26),  # zijdelt-dominant (lateraal+achter)
    "Biceps":    (4, 6,  14, 20, 26),
    "Triceps":   (4, 6,  10, 14, 18),
    "Billen":    (0, 0,  6,  12, 16),  # MEV 0 (besluit Bas 12 juni): billen krijgen ALLEEN
                                       #   direct werk in hun focus-cyclus of als voorkeurspier;
                                       #   leunt op hinge/squat-spillover. Vrouw: via voorkeur.
    "Kuiten":    (4, 4,  8,  16, 20),  # MEV op 4 (= handwerk-accessoiredosis)
    "Core":      (0, 3,  10, 16, 20),  # MEV op 3 (= handwerk-accessoiredosis)
    "Onderrug":  (0, 2,  4,  8,  12),  # MV-niveau: onderrug krijgt veel indirect via hinge;
                                       #   2 directe sets = handwerk (was te hoog op 6)
    "Adductoren": (0, 2,  2,  4,  6),  # TAAK E (besluit Bas 14 juni): binnenbeen als eigen
                                       #   accessoire. Lage onderhoudsdosis (2 sets), ALLEEN voor
                                       #   Gevorderd/Expert (zie ADDUCTOREN_MIN_ERVARING). Novice=0.
}
# TAAK E: Adductoren krijgt alleen volume bij voldoende ervaring. Mechanisme voor
# ervaring-gated accessoire-dosis (nieuw in v1.9.2). Novice -> 0 sets, anders 2.
ADDUCTOREN_VASTE_DOSIS = 2
ADDUCTOREN_MIN_ERVARING = ("Gevorderd", "Expert")  # Novice krijgt 0
# Doel-DIRECT-volume per krachtniveau, per spier, als index in de landmark-tuple.
# BEG -> MEV (onderkant, beginners groeien op weinig); INT -> MAV-laag; ADV -> MAV-hoog.
LANDMARK_INDEX = {"BEG": 1, "INT": 2, "ADV": 3}  # 1=MEV, 2=MAV-laag, 3=MAV-hoog
MRV_INDEX = 4  # harde bovengrens (totaal-effectief) ongeacht budget

# TAAK A (besluit Bas 14 juni): voor VROUWEN is Billen een HOOFDSPIER (laag-1) met eigen
# landmarks i.p.v. de mannelijke accessoire-tuple (0,0,6,12,16). GEEN hogere getallen dan een
# normale primaire spier: de bilspier is anatomisch identiek tussen seksen (MRI, genormaliseerd
# geen verschil). Deze tuple spiegelt een gemiddelde primaire spier (orde quads/hams). Het
# sekseverschil in werkcapaciteit zit AL in de sessie-cap (+2), niet hier — geen dubbeltelling.
# STARTwaarden, te kalibreren in taak C op echte engine-output.
RP_LANDMARKS_BILLEN_VROUW = (4, 8, 12, 16, 20)

def billen_landmark(geslacht):
    """Geeft de Billen-landmark-tuple, geslacht-bewust. Vrouw -> primaire-spier-landmarks."""
    if _lc(geslacht).startswith("v"):
        return RP_LANDMARKS_BILLEN_VROUW
    return RP_LANDMARKS["Billen"]

# Per-sessie junk-grens: max direct volume per spier per sessie (Beardsley/Krieger:
# hypertrofie plateaut ~6-8 directe sets/spier/sessie). Boven deze grens wordt extra
# volume naar een andere dag geduwd; meer trainingsdagen = meer totaalvolume kwijt.
SESSIE_SPIER_CAP = 8

PREHAB_SETS = 2  # SOP par.4 / par.12

# Re-entry-volumeband per krachtniveau (besluit 11 juni, gekoppeld aan landmark-model):
# bij BEG is het volume al MEV-niveau -> re-entry cap't vooral oefeningen + intensiteit
# (SOP par.1-RE), geen extra volume-knip. Bij INT/ADV wel terug richting MEV.
RE_ENTRY_VOLUME = {"BEG": 1.0, "INT": 0.80, "ADV": 0.80}
VROUW_CAP_BONUS = 2          # besluit Bas 14 juni: +2 sessie-cap. Vrouwen herstellen sneller TUSSEN
                             # SETS (Nuckols/PeerJ 2026, bench press), dus meer werkvolume past in
                             # dezelfde sessietijd. Sessie-cap, NIET weektotaal. Bewijs vnl. bench-press
                             # = werkhypothese overige spiergroepen. ~+6-7% bij cap 27-34.
VOORKEUR_LEAN = 2.0          # besluit Bas 11 juni: voorkeurspier +2 TE (matcht handwerk)

# DEFINITIEF (SOP v3.2 par.6, verbatim hersteld uit Capaciteit-Fundament v2 via chat-historie 9 juni):
# (fase, volume_multiplier, intensiteit-sturing)
WEEK_FASEN = {
    "BEG": [("skill/techniek", 0.65, "rep-targets; licht, beweging leren"),
            ("skill/techniek", 0.65, "rep-targets; licht, beweging leren"),
            ("belasting opbouwen", 0.80, "double progression op rep-targets"),
            ("belasting opbouwen", 0.80, "double progression op rep-targets"),
            ("doorbouwen", 0.90, "rep-targets; RIR-richtlijn: laat 3-4, nooit grinden"),
            ("doorbouwen", 1.00, "rep-targets; RIR-richtlijn: laat 3-4, nooit grinden"),
            ("piek", 1.00, "volle capaciteit, techniek leidend; nooit grinden"),
            ("evaluatie", 0.70, "hertest sleutellifts + techniek")],
    "INT": [("calibratie", 0.75, "RIR comp 3-4 / iso 2-3"),
            ("opbouw", 0.90, "RIR comp 2-3 / iso 1-2"),
            ("piek volume", 1.00, "RIR comp 2 / iso 1"),
            ("intensiteitspiek", 1.00, "RIR comp 1 / iso 0-1"),
            ("final push", 1.00, "RIR comp 1 / iso 0"),
            ("deload/evaluatie", 0.50, "RIR 4-5; 0.7x bij lage volume-band")],
    "ADV": [("calibratie", 0.80, "RIR comp 2-3 / iso 1-2"),
            ("opbouw", 0.95, "RIR comp 1-2 / iso 1"),
            ("piek volume", 1.00, "RIR comp 1 / iso 0-1"),
            ("intensiteitspiek", 1.00, "RIR comp 0-1 / iso 0"),
            ("deload", 0.50, "RIR 4-5")],
}

# GEVERIFIEERD tegen bibliotheek v1.4 (10 juni): patronen matchen Barbell Bench Press,
# Barbell Back Squat en Sumo Deadlift. NB: de bibliotheek bevat GEEN conventionele
# barbell deadlift (alleen Sumo + RDL/SLDL, die terecht uitgesloten zijn).
BIG3_PATRONEN = ["barbell back squat", "barbell squat", "barbell front squat",
                 "barbell bench press", "conventional deadlift", "sumo deadlift"]
BIG3_UITSLUITEN = ["romanian", "rdl", "stiff"]

# GEVERIFIEERD tegen bibliotheek v1.4 tag-vocab; "basis"-set afgeleid uit het
# materiaal van Owens referentie-schema (standaard-gym: vrije gewichten, kabels,
# gangbare machines; GEEN specialty: smith/pec deck/pendulum/landmine/preacher/
# dip station/hip-thrust-machine/reverse pec deck/assisted pull-up/ab wheel).
# TER BEVESTIGING door Bas — intake krijgt later een echte materiaal-checklist (SOP par.15).
PROFIEL_MATERIAAL = {
    "commercieel": None,  # None = alles beschikbaar (full-service gym)
    "basis": ["barbell", "dumbbell", "cable", "bodyweight", "bench", "rack",
              "pullup_bar", "lat_pulldown", "leg_press", "leg_curl", "leg_extension",
              "row_machine", "calf_machine", "hack_squat", "machine"],
    # BASIC FIT (11 juni, n.a.v. Romme): realistische standaard-inventaris.
    # WEL: smith, pers-machines, pec deck (combi met reverse), assisted pull-up,
    # dips, preacher, EZ. NIET: pendulum, landmine, hip-thrust-machine, ab wheel.
    # TER BEVESTIGING door Bas; de intake-materiaalchecklist (SOP par.15) vervangt
    # dit profiel per vestiging.
    "basic_fit": ["barbell", "dumbbell", "cable", "bodyweight", "bench", "rack",
                  "pullup_bar", "lat_pulldown", "leg_press", "leg_curl", "leg_extension",
                  "row_machine", "calf_machine", "hack_squat", "machine", "smith",
                  "chest_press_machine", "shoulder_press_machine", "pec_deck",
                  "reverse_pec_deck", "assisted_pullup", "dip_station",
                  "preacher_bench", "ez_bar"],
}
# Specialty-oefeningen die de GENERIEKE 'machine'-tag dragen maar in budget-gyms
# ontbreken (bibliotheek-hertagging gewenst; dit is de pleister op engine-niveau).
PROFIEL_UITSLUIT_NAMEN = {
    "basis": ["reverse hyperextension", "glute-ham raise"],
    "basic_fit": ["reverse hyperextension", "glute-ham raise"],
}

# ----------------------------- HULPFUNCTIES ---------------------------------

def _lc(x):
    return str(x or "").lower()


def seed_int(*delen):
    h = hashlib.md5("|".join(str(d) for d in delen).encode("utf-8")).hexdigest()
    return int(h[:8], 16)


def is_big3(oef):
    naam = _lc(oef.get("naam"))
    if any(u in naam for u in BIG3_UITSLUITEN):
        return False
    return any(p in naam for p in BIG3_PATRONEN)


def is_unilateraal(oef):
    v = oef.get("unilateraal")
    return v is True or _lc(v) in ("ja", "true", "1", "yes")


def heeft_tag(oef, veld, *zoek):
    waarde = _lc(oef.get(veld))
    return any(z in waarde for z in zoek)

# ----------------------------- B1: CLASSIFICATIE ----------------------------

def classificeer(intake, flags):
    """SOP par.1: twee losse assen + re-entry-overlay. Kracht op geschatte 1RM (par.1-1RM)."""
    bw = float(intake.get("lichaamsgewicht") or 0)
    lifts = intake.get("lifts") or {}
    geslacht = "vrouw" if _lc(intake.get("geslacht", "M")).startswith("v") else "man"
    drempels = KRACHTDREMPELS[geslacht]
    if geslacht == "vrouw":
        pass  # row heeft geen vrouw-drempel; valt automatisch buiten de loop
    niveaus = []
    row_tier = None
    for lift in ("bench", "squat", "deadlift", "row"):
        w = lifts.get(lift)
        if w in (None, "", 0):
            continue
        if lift == "row" and "row" not in drempels:
            continue  # vrouw: row heeft geen drempel
        if isinstance(w, dict):  # {"kg": x, "reps": n}
            rm = schat_1rm(w.get("kg", 0), w.get("reps", 8), flags)
        else:
            # Kale getallen worden per intake-conventie als 8RM-werkgewicht gelezen
            # (werkorder: "Lifts zijn 8RM-werkgewichten, geen 1RM").
            rm = schat_1rm(w, 8, flags)
        if not bw:
            continue
        ratio = rm / bw
        d_int, d_adv = drempels[lift]
        tier = "ADV" if ratio >= d_adv else "INT" if ratio >= d_int else "BEG"
        if lift == "row":
            row_tier = tier  # bonussignaal: niet in de mediaan
        else:
            niveaus.append(tier)
    if len(niveaus) < 2:
        kracht = "BEG"
        flags.append("INSUFFICIENT_STRENGTH_DATA")
    else:
        volgorde = {"BEG": 0, "INT": 1, "ADV": 2}
        niveaus.sort(key=lambda n: volgorde[n])
        kracht = niveaus[len(niveaus) // 2]  # mediaan over SBD
        alle_vier = niveaus + ([row_tier] if row_tier else [])
        if len(alle_vier) >= 4 and all(n == "ADV" for n in alle_vier):
            kracht = "ADV"  # SOP v3.2 par.1: 4/4 ADV-ratio's -> kracht ADV
            flags.append("EXCEPTIONAL_STRENGTH")
    ervaring = ERVARING_UIT_BUCKET.get(intake.get("ervaring_bucket", "<1"), "Novice")
    if ervaring == "Expert" and not intake.get("progressie_tracking", False):
        ervaring = "Gevorderd"
    re_entry = bool(intake.get("re_entry", False))
    re_entry_type = _lc(intake.get("re_entry_type", "blessure"))  # default: blessure-variant
    if re_entry:
        flags.append("RE_ENTRY_ACTIEF")
    if kracht != "BEG" and ervaring == "Novice":
        flags.append("KRACHT_ERVARING_MISMATCH_INFO")
    effectieve_ervaring = ervaring
    if re_entry and re_entry_type != "detraining":
        # Blessure-/revalidatie-variant: pool gecapt op Novice (of een tier onder echt niveau).
        effectieve_ervaring = "Novice" if ervaring == "Novice" else \
            list(ERVARING_RANG)[max(0, ERVARING_RANG[ervaring] - 1)]
    # Detraining-variant (SOP par.1-RE): "bekende compounds mogen blijven, oefening-cap milder"
    # -> geen tier-verlaging; alleen de volume-reductie + zachtere opbouw geldt.
    return kracht, ervaring, effectieve_ervaring, re_entry

# ----------------------------- C1: CAPACITEIT -------------------------------

def sessie_cap(minuten, geslacht, kracht):
    """SOP par.3: tijd-cap + vrouw-bonus. Het herstel-plafond werkt op WEEKNIVEAU
    (besluit 11 juni) en wordt in genereer() toegepast. Big3-straf volgt na selectie."""
    sleutel = min(BASIS_CAP, key=lambda m: abs(m - int(minuten)))
    cap = BASIS_CAP[sleutel]
    if _lc(geslacht).startswith("v"):
        cap += VROUW_CAP_BONUS
    return cap

# ----------------------------- C2 + B3: VERDELING ---------------------------

def landmark_doel(spier, kracht):
    """Doel-TOTAAL-EFFECTIEF volume per spier per krachtniveau, uit RP-landmarks."""
    lm = RP_LANDMARKS[spier]
    return lm[LANDMARK_INDEX[kracht]], lm[MRV_INDEX]  # (doel_TE, mrv)


def knip_volume(direct, accessoire, tekort, kracht, focus_accessoire, flags):
    """Knip 'tekort' sets uit het weekplan volgens de besloten hierarchie (11 juni #5):
    1) focus-accessoire-surplus -> baseline, 2) Core -> weekminimum, 3) overige
    accessoires -> 2, 4) primaire spieren naar MEV-doel (armen DIRECT_DOEL_HARD hard
    beschermd). Muteert direct/accessoire in-place; returnt resterend tekort."""
    if tekort <= 0:
        return 0
    if focus_accessoire in accessoire:
        lm = RP_LANDMARKS[focus_accessoire]
        basis_min = max(2, int(lm[1]))
        if focus_accessoire == "Core":
            basis_min = max(CORE_WEEK_MINIMUM, basis_min)
        geef = min(accessoire[focus_accessoire] - basis_min, tekort)
        if geef > 0:
            accessoire[focus_accessoire] -= geef
            tekort -= geef
    if tekort > 0 and accessoire.get("Core", 0) > CORE_WEEK_MINIMUM:
        geef = min(accessoire["Core"] - CORE_WEEK_MINIMUM, tekort)
        accessoire["Core"] -= geef
        tekort -= geef
    if tekort > 0:
        for sp in ("Onderrug", "Kuiten", "Billen"):
            if tekort <= 0:
                break
            ondergrens = 0 if sp == "Billen" else 2
            if accessoire.get(sp, 0) > ondergrens:
                geef = min(accessoire[sp] - ondergrens, tekort)
                accessoire[sp] -= geef
                tekort -= geef
    while tekort > 0:
        kandidaten = [m for m in direct
                      if direct[m] > max(2, DIRECT_DOEL_HARD.get(m, 0))]
        if not kandidaten:
            # STAP 5 (extreem randgeval, bv. 2x45min): de floor-som past niet in de
            # tijd. Dan wordt BEWUST een spier geofferd, in deze volgorde — spieren
            # die via spillover/prehab al gedekt worden eerst. Nooit stilletjes.
            for offer in ("Billen", "Onderrug", "Schouders", "Kuiten"):
                doelwit = direct if offer in direct else accessoire
                if doelwit.get(offer, 0) > 0:
                    tekort -= doelwit[offer]
                    doelwit[offer] = 0
                    flags.append(f"GEOFFERD_BIJ_TIJDNOOD_{offer}")
                    break
            else:
                flags.append("TIJD_KORT_NA_BESCHERMDE_FLOORS")
                break
            continue
        def overschot(m):
            doel_te, _ = landmark_doel(m, kracht)
            return (direct[m] + SPILLOVER.get(m, 0) * 0.5) - doel_te
        kies = max(kandidaten, key=overschot)
        direct[kies] -= 1
        tekort -= 1
    return tekort


def verdeel_volume(weekbudget, voorkeur, kracht, flags, focus_accessoire=None,
                   houding_focus=False, geslacht="M", ervaring="Gevorderd"):
    """SOP par.4 herzien (besluiten 11 juni): per-spier MEV->MRV-landmarks i.p.v. weektotaal-cap.
    BESLUIT #5: Billen telt als accessoire (man) en draait mee in de accessoire-rotatie:
    per cyclus krijgt EEN accessoire (Billen/Kuiten/Core/Onderrug) de focus (MAV-laag),
    de rest baseline (MEV). Core heeft een hard weekminimum (CORE_WEEK_MINIMUM).
    Trim-hierarchie bij tijdsdruk: 1) focus-surplus terug naar baseline, 2) Core naar
    weekminimum, 3) primaire spieren via overschot-logica (armen hard beschermd).
    Levert (primair_direct, accessoire_direct, diagnostiek)."""
    import math
    direct = {}
    diag = {"focus_accessoire": focus_accessoire}
    is_vrouw = _lc(geslacht).startswith("v")
    # TAAK A: voor vrouwen is Billen een hoofdspier -> NIET overslaan in de primair-loop,
    # en niet als accessoire roteren. Voor mannen ongewijzigd (accessoire-route).
    bil_is_primair_vrouw = is_vrouw  # Billen telt voor vrouwen als volwaardige primaire spier
    for spier in PRIMAIR:
        if spier in ACCESSOIRE_ROTATIE and spier != voorkeur:
            if spier == "Billen" and bil_is_primair_vrouw:
                pass  # vrouw: Billen NIET overslaan, behandel als primaire spier
            else:
                continue  # Billen (man): volume via accessoire-rotatie (tenzij voorkeurspier)
        # geslacht-bewuste landmark voor Billen (vrouw krijgt primaire-spier-landmarks)
        if spier == "Billen":
            lm_s = billen_landmark(geslacht)
            doel_te, mrv = lm_s[LANDMARK_INDEX[kracht]], lm_s[MRV_INDEX]
        else:
            doel_te, mrv = landmark_doel(spier, kracht)
        indirect = SPILLOVER.get(spier, 0.0)
        # BESLUIT #1: armen krijgen een HARD direct-doel (stubborn-muscle-regel).
        if spier in DIRECT_DOEL_HARD:
            d = DIRECT_DOEL_HARD[spier]
        else:
            disc = SPILLOVER_KWALITEIT.get(spier, 1.0)
            gratis_te = indirect * 0.5 * disc
            d = max(2, int(math.ceil(doel_te - gratis_te)))
        max_direct_mrv = int(math.floor(mrv - indirect * 0.5))
        d = min(d, max(2, max_direct_mrv))
        direct[spier] = d
        diag[spier] = {"doel_te": doel_te, "mrv": mrv, "direct": d,
                       "te_geleverd": round(d + indirect * 0.5, 1)}
    # voorkeurspier: +lean direct (binnen MRV). Geldt ook als de voorkeur een
    # rotatie-accessoire is (bv. Billen bij vrouw, SOP par.11): die draait dan als
    # primaire spier op MAV-laag + lean i.p.v. baseline.
    if voorkeur in PRIMAIR:
        if voorkeur in ACCESSOIRE_ROTATIE and not (voorkeur == "Billen" and bil_is_primair_vrouw):
            lm = RP_LANDMARKS[voorkeur]
            basis = lm[2]  # MAV-laag: voorkeur-accessoire traint als prioriteit
            direct[voorkeur] = basis
            diag[voorkeur] = {"doel_te": basis, "mrv": lm[MRV_INDEX], "direct": basis}
        # geslacht-bewuste landmark voor Billen-voorkeur (vrouw: al primair in de loop hierboven)
        if voorkeur == "Billen":
            lm_v = billen_landmark(geslacht)
            doel_te, mrv = lm_v[LANDMARK_INDEX[kracht]], lm_v[MRV_INDEX]
            sp_v = SPILLOVER.get(voorkeur, 0)
            max_direct_mrv = int(math.floor(mrv - sp_v * 0.5))
        else:
            doel_te, mrv = landmark_doel(voorkeur, kracht)
            max_direct_mrv = int(math.floor(mrv - SPILLOVER.get(voorkeur, 0) * 0.5))
        direct[voorkeur] = min(direct[voorkeur] + int(VOORKEUR_LEAN), max(2, max_direct_mrv))
        diag[voorkeur]["direct"] = direct[voorkeur]
        diag[voorkeur]["voorkeur_lean"] = True
    # ACCESSOIRE-ROTATIE (besluit #5): baseline = MEV; focus-accessoire = MAV-laag.
    accessoire = {}
    for spier in ACCESSOIRE_ROTATIE:
        if spier == voorkeur:
            continue  # zit al in direct (voorkeur-route)
        if spier == "Billen" and bil_is_primair_vrouw:
            continue  # vrouw: Billen is primair (al in direct), niet als accessoire
        lm = RP_LANDMARKS[spier]
        basis = int(lm[1])                              # MEV-baseline (Billen: 0)
        if spier == "Core":
            basis = max(CORE_WEEK_MINIMUM, basis)       # core ALTIJD aanwezig
        if focus_accessoire == spier:
            # FIX 12 juni (Bas): focus-bump SCHAALT met krachtniveau. Een beginner
            # die 'core-focus' krijgt hoort geen volle MAV (10) te draaien — dat is
            # te veel volume voor cyclus 1 en verdringt fundamenteler werk. BEG pakt
            # het midden tussen MEV en MAV, INT ~3/4, ADV de volle MAV-laag.
            mev_l, mav_l = int(lm[1]), int(lm[2])
            if kracht == "BEG":
                doel = mev_l + (mav_l - mev_l) // 2
            elif kracht == "INT":
                doel = mev_l + (3 * (mav_l - mev_l)) // 4
            else:
                doel = mav_l
            basis = max(basis, doel)
            diag[spier + "_focus"] = basis
        accessoire[spier] = basis
    # TAAK E: Adductoren (binnenbeen) als ervaring-gated accessoire. Staat NIET in de
    # focus-rotatie (besluit Bas). Novice -> 0 (geen volume EN de enige oefening is Gevorderd,
    # dus geen verdampend volume); Gevorderd/Expert -> vaste lage dosis.
    if ervaring in ADDUCTOREN_MIN_ERVARING:
        accessoire["Adductoren"] = ADDUCTOREN_VASTE_DOSIS
        diag["adductoren_dosis"] = ADDUCTOREN_VASTE_DOSIS
    else:
        diag["adductoren_dosis"] = 0  # Novice: geen binnenbeen-isolatie
    # tijdbudget de luxe toelaat — focus is luxe en gaat eerst bij tijdnood (hierarchie).
    if houding_focus and "Schouders" in direct:
        ruimte_check = weekbudget - sum(accessoire.values()) - PREHAB_SETS \
            - sum(direct.values())
        _, mrv_s = landmark_doel("Schouders", kracht)
        max_s = int(mrv_s - SPILLOVER.get("Schouders", 0) * 0.5)
        if ruimte_check >= 2 and direct["Schouders"] + 2 <= max_s:
            direct["Schouders"] += 2
            diag["houding_focus_bump"] = 2
    # tijd-budget als SECUNDAIRE begrenzer: knip via de besloten hierarchie.
    primair_som = sum(direct.values())
    beschikbaar_primair = weekbudget - sum(accessoire.values()) - PREHAB_SETS
    if primair_som > beschikbaar_primair:
        flags.append("TIJDBUDGET_KNELT_ONDER_LANDMARK")
        knip_volume(direct, accessoire, primair_som - beschikbaar_primair,
                    kracht, focus_accessoire, flags)
    return direct, accessoire, diag

# ----------------------------- B2: SPLIT & DAGEN ----------------------------

def split_template(dagen):
    if dagen <= 2:
        return [("Full Body A", "FULL"), ("Full Body B", "FULL")][:max(1, dagen)]
    if dagen == 3:
        return [("Upper", "UPPER"), ("Lower", "LOWER"), ("Full Body", "FULL")]
    if dagen == 4:
        return [("Upper 1", "UPPER"), ("Lower 1", "LOWER"),
                ("Upper 2", "UPPER"), ("Lower 2", "LOWER")]
    # 5-daags PPLUL (besluit Bas 12 juni): klassiek Push/Pull/Legs + Upper/Lower.
    # Bovenlijf 3x (Push, Pull, Upper), benen 2x (Legs, Lower).
    return [("Push", "PUSH"), ("Pull", "PULL"), ("Legs", "LEGS"),
            ("Upper", "UPPER"), ("Lower", "LOWER")]


DAG_SPIEREN = {
    "FULL": PRIMAIR + ["Kuiten", "Core", "Onderrug", "Adductoren"],
    "UPPER": ["Rug", "Borst", "Schouders", "Biceps", "Triceps", "Core"],
    "LOWER": ["Quads", "Hams", "Billen", "Kuiten", "Onderrug", "Core", "Adductoren"],
    # PPLUL (5-daags, besluit Bas 12 juni): klassiek Push/Pull/Legs + Upper/Lower.
    "PUSH": ["Borst", "Schouders", "Triceps", "Core"],
    "PULL": ["Rug", "Biceps", "Core"],
    "LEGS": ["Quads", "Hams", "Billen", "Kuiten", "Onderrug", "Core", "Adductoren"],
}
# Dagtypes met benenwerk (guardrail + leg-opener + hinge/curl-regel gelden hier):
BEEN_DAGTYPES = ("FULL", "LOWER", "LEGS")


def verdeel_over_dagen(volume, dagen_types, dag_cap=None):
    """Breedte-gewogen dag-verdeling (HERZIEN 12 juni 2026 — option 2, Bas).

    KERNPRINCIPE: het aandeel van een spier op een dag is omgekeerd evenredig met
    hoeveel spiergroepen die dag bestrijkt. Een brede 'Full Body'-dag (11 spieren)
    krijgt dus per spier minder dan een gerichte Upper/Lower-dag (6 spieren).
    Gevolg: in U/L/FB wordt FB automatisch de LICHTERE derde touch; de dedicated
    dagen dragen het hoofdvolume (en daarmee de klant-prioriteit). Bij symmetrische
    splits (FB-A/FB-B, of Upper1/Upper2) zijn de dag-gewichten gelijk -> 50/50.

    Behoudt: beschermde spieren (Core+armen) eerst, brokken >=2 (geen 1-set
    splinters), cap-bewustheid. Returnt (per_dag, onplaatsbaar)."""
    ACC_VOORKEUR = {"Kuiten": "LOWER", "Onderrug": "LOWER"}
    per_dag = [defaultdict(int) for _ in dagen_types]
    dag_tot = [0] * len(dagen_types)
    onplaatsbaar = 0

    def breedte(t):
        # aantal PRIMAIRE spiergroepen dat de dag bestrijkt (Core telt niet mee:
        # die zit op elke dag en zou alle gewichten gelijk vertekenen).
        spieren = DAG_SPIEREN.get(t, [])
        n = len([s for s in spieren if s != "Core"])
        return n or 6

    def daggewicht(t):
        return 1.0 / breedte(t)

    def ruimte(j):
        return (dag_cap - dag_tot[j]) if dag_cap else 10**6

    BEEN_DEDICATED = ("LOWER", "LEGS")  # dedicated benen-dag (krijgt hams hinge+curl)

    beschermd = ["Core"] + [m for m in DIRECT_DOEL_HARD if m in volume]
    volgorde = sorted(volume.items(),
                      key=lambda kv: (0 if kv[0] in beschermd else 1, -kv[1], kv[0]))

    for spier, sets_week in volgorde:
        sw = int(sets_week)
        if sw <= 0:
            continue
        idx = [i for i, t in enumerate(dagen_types) if spier in DAG_SPIEREN[t]]
        if not idx:
            idx = list(range(len(dagen_types)))

        # ---- frequentiebepaling ----
        # 1x bij klein volume (<=3) of pure 1x-accessoire (Onderrug); anders 2x mits
        # er >=2 dagen zijn EN elke dag dan >=2 sets kan krijgen (min-2, geen splinter).
        if sw <= 3 or spier == "Onderrug":
            freq = 1
        elif len(idx) >= 2 and sw >= 4:
            freq = 2
        else:
            freq = 1

        # ---- HAMS-regel (besluit Bas 12 juni): dedicated benen-dag krijgt hinge+curl
        # (dus >=4 sets daar), FB/secundair krijgt een hinge (>=2). Forceer 2x als er
        # genoeg volume is, met de dedicated dag als zwaartepunt. ----
        hams_dedicated = None
        if spier == "Hams":
            ded = [i for i in idx if dagen_types[i] in BEEN_DEDICATED]
            if ded:
                hams_dedicated = ded[0]
                if sw >= 6 and len(idx) >= 2:
                    freq = 2  # 2x: dedicated >=4 (hinge+curl) + secundair rest
                elif sw >= 4:
                    freq = 1  # alles op dedicated dag (hinge+curl), geen splinter elders

        if freq == 1:
            # plaats op de dag met HOOGSTE gewicht (meest gerichte) met ruimte.
            if hams_dedicated is not None:
                i = hams_dedicated
            else:
                pref = ACC_VOORKEUR.get(spier)
                kand = [i for i in idx if dagen_types[i] == pref and ruimte(i) >= sw] or \
                       [i for i in idx if ruimte(i) >= sw] or idx
                i = max(kand, key=lambda j: (daggewicht(dagen_types[j]), -dag_tot[j]))
            plaats = min(sw, max(0, ruimte(i))) if dag_cap else sw
            if spier == "Core":
                plaats = max(plaats, min(sw, CORE_WEEK_MINIMUM))
            if plaats < 2 and spier != "Core":
                plaats = 0
            per_dag[i][spier] += plaats
            dag_tot[i] += plaats
            onplaatsbaar += sw - plaats
            continue

        # ---- freq == 2: MIN-2-VLOER per dag, geen 1-set splinters (besluit Bas) ----
        # Kies 2 dagen: hoogste gewicht eerst (bij gelijk: minst belast). Voor hams
        # is de dedicated dag altijd dag 1.
        kand = sorted(idx, key=lambda j: (-daggewicht(dagen_types[j]), dag_tot[j], j))
        if hams_dedicated is not None:
            kand = [hams_dedicated] + [j for j in kand if j != hams_dedicated]
        gekozen = kand[:2]
        # cap-check: past 2+2 niet, val terug op 1 dag. STRENGER (fix 15 juni): vereis dat
        # ELKE gekozen dag >=2 ruimte heeft, niet alleen de som — anders ontstaat een 1-set
        # splinter op de dag met te weinig ruimte (SOP: min-2-vloer, geen splinters).
        if dag_cap and min(max(0, ruimte(gekozen[0])),
                           max(0, ruimte(gekozen[1]))) < 2:
            gekozen = [max(gekozen, key=ruimte)]
        if len(gekozen) == 1:
            i = gekozen[0]
            plaats = min(sw, max(0, ruimte(i))) if dag_cap else sw
            if plaats < 2:
                plaats = 0
            per_dag[i][spier] += plaats
            dag_tot[i] += plaats
            onplaatsbaar += sw - plaats
            continue

        gewichten = [daggewicht(dagen_types[j]) for j in gekozen]
        symmetrisch = len({round(g, 6) for g in gewichten}) == 1
        # zwaarste-gewicht dag eerst
        gekozen = sorted(gekozen, key=lambda j: -daggewicht(dagen_types[j]))
        # start: 2 op elke dag (de min-2-vloer)
        toegekend = {j: 2 for j in gekozen}
        extra = sw - 4
        # hams dedicated dag wil >=4: geef die eerst genoeg om hinge+curl te halen
        if hams_dedicated is not None and extra > 0:
            j0 = gekozen[0]
            bonus = min(extra, 2)  # naar 4 op de dedicated dag
            toegekend[j0] += bonus
            extra -= bonus
        # rest naar gewicht (zwaarste dag eerst), cap-bewust
        if extra > 0:
            wsum = sum(gewichten)
            verdeeld = 0
            for k, j in enumerate(gekozen):
                if k == len(gekozen) - 1:
                    deel = extra - verdeeld
                elif symmetrisch:
                    deel = (sw - 4) // 2
                else:
                    deel = round((sw - 4) * daggewicht(dagen_types[j]) / wsum)
                deel = max(0, deel)
                toegekend[j] += deel
                verdeeld += deel
        # cap toepassen + plaatsen
        for j in gekozen:
            gewenst = min(toegekend[j], SESSIE_SPIER_CAP)
            plaatsbaar = min(gewenst, max(0, ruimte(j))) if dag_cap else gewenst
            if plaatsbaar < 2 and spier != "Core":
                plaatsbaar = 0  # vangnet (fix 15 juni): nooit een 1-set splinter plaatsen
            per_dag[j][spier] += plaatsbaar
            dag_tot[j] += plaatsbaar
            onplaatsbaar += max(0, toegekend[j] - plaatsbaar)
    return per_dag, onplaatsbaar

# ----------------------------- B5: SELECTIE-MOTOR ---------------------------

def _tags(waarde):
    """Normaliseer een tag-veld (lijst of string) naar een set lowercase tags."""
    if isinstance(waarde, (list, tuple)):
        return {_lc(t) for t in waarde}
    return {t.strip() for t in _lc(waarde).replace(";", ",").split(",") if t.strip()}


def materiaal_ok(oef, intake):
    """EXACTE tag-match (geen substring: 'machine' mag niet 'hip_thrust_machine' matchen)."""
    oef_tags = _tags(oef.get("materiaal"))
    expliciet = intake.get("materiaal_beschikbaar")
    if expliciet:
        return bool(oef_tags & {_lc(m) for m in expliciet})
    profiel = _lc(intake.get("materiaal_profiel", "commercieel"))
    for verboden in PROFIEL_UITSLUIT_NAMEN.get(profiel, []):
        if verboden in _lc(oef.get("naam")):
            return False
    toegestaan = PROFIEL_MATERIAAL.get(profiel, None)
    if toegestaan is None:
        return True
    # ALLE benodigde tags moeten beschikbaar zijn (bench-press vereist barbell EN rack EN bench)
    return oef_tags <= set(toegestaan)


# Opbouw-oefeningen: technisch/stabiliteits-intensief — NOOIT in cyclus 1, daar
# bouw je naartoe (besluit Bas 12 juni). TODO: wordt bibliotheekveld bij de doorname.
NIET_CYCLUS_1 = ("bulgarian split squat",)

# TAAK F-vervolg (15 juni): blessure-invoer is vrije tekst van de coach. Exacte token-match
# laat varianten lekken ("knieën"/"knieblessure"/"lage rug"/"rugpijn"). Daarom een synoniem-map:
# per canonieke contra-indicatie (zoals in de bibliotheek getagd) een set trefwoorden die als
# SUBSTRING in de blessure-tekst gezocht worden. Zo matcht "lage rugklachten" -> onderrug,
# "knieblessure" -> knie, "tenniselleboog" -> elleboog, enz.
BLESSURE_SYNONIEMEN = {
    "knie":     ("knie", "meniscus", "patella", "acl", "vkb", "kruisband"),
    "schouder": ("schouder", "rotator", "cuff", "labrum", "ac-gewricht", "ac gewricht",
                 "impingement", "bicepspees"),
    "elleboog": ("elleboog", "epicond", "tennisarm", "golfersarm", "golferselleboog"),
    "pols":     ("pols", "carpaal", "carpal", "tfcc", "duim"),
    "onderrug": ("onderrug", "rug", "lumbaal", "lumbal", "hernia", "spit", "ischias",
                 "si-gewricht", "si gewricht", "bekken"),
}


def actieve_blessure_contra(intake):
    """Bepaal welke canonieke contra-indicaties actief zijn op basis van de vrije
    blessure-tekst (substring-match op synoniemen). Plus losse tokens (>=3 chars) voor
    eventuele andere/toekomstige tags. Robuust tegen meervoud, samenstellingen en spelling."""
    import re as _re
    tekst = " ".join(_lc(b) for b in (intake.get("blessures") or []))
    actief = set()
    for canon, kws in BLESSURE_SYNONIEMEN.items():
        if any(kw in tekst for kw in kws):
            actief.add(canon)
    actief |= {t for t in _re.findall(r"[a-zà-ÿ]+", tekst) if len(t) >= 3}
    return actief


def harde_filters(bib, spier, intake, effectieve_ervaring, cyclus=None):
    """SOP par.8 laag 1."""
    rang = ERVARING_RANG[effectieve_ervaring]
    dislikes = [_lc(d) for d in (intake.get("dislikes") or [])]
    dislikes += [_lc(p) for p in (intake.get("pijnlijke_oefeningen") or [])]
    # Blessures tokenizen: "lies (onbevestigd)" -> {"lies", "onbevestigd"}, zodat
    # vrije intake-tekst op de contra-tags van de bibliotheek kan matchen.
    # Blessures -> actieve contra-indicaties (synoniem-bewust, substring-match). Vangt
    # "lage rug"/"knieblessure"/"tenniselleboog"/"polsblessure" enz. correct af.
    blessure_tokens = actieve_blessure_contra(intake)
    pool = []
    for oef in bib:
        if _lc(oef.get("primaire_spier")) != _lc(spier):
            continue
        if ERVARING_RANG.get(oef.get("techniek_niveau", "Expert"), 2) > rang:
            continue
        nov = oef.get("novice_only")
        if (nov is True or _lc(nov) in ("ja", "true")) and effectieve_ervaring != "Novice":
            continue
        naam = _lc(oef.get("naam"))
        if cyclus == 1 and any(t in naam for t in NIET_CYCLUS_1):
            continue
        # Kuiten nooit met dumbbell (besluit Bas 12 juni): altijd machine/smith/
        # leg press. Bibliotheek v1.5 heeft de DB-entries al verwijderd; borging.
        if spier == "Kuiten" and "dumbbell" in _tags(oef.get("materiaal")):
            continue
        if any(d and d in naam for d in dislikes):
            continue
        contra_tags = _tags(oef.get("contra_indicaties"))
        if blessure_tokens & contra_tags:
            continue
        if not materiaal_ok(oef, intake):
            continue
        pool.append(oef)
    return pool


def structuur_filter(pool, spier, dag_type, week_patronen):
    """SOP par.8 laag 2: patroonbalans, spillover-regio, leg-day-regels."""
    if spier == "Schouders":
        # F3 (15 juni): op FULL BODY-dagen mag schouder een overhead press (compound) zijn.
        # Een FB-dag heeft minder borst-pers-volume dan een Upper-dag, dus geen overlap-
        # probleem; liefst een compound, anders een side/rear-delt. Front raise blijft uit.
        # pijnlijke_oefeningen/blessures (bv. pols -> Overhead Press) filtert harde_filters al.
        if dag_type == "FULL":
            sub = [o for o in pool if "front raise" not in _lc(o.get("naam"))]
            return sub or pool
        # Niet-FB (Upper/Push): spillover-regio = lateraal/achter. GEEN pers EN GEEN front
        # raise — de voorste delt krijgt al volop pers-spillover.
        sub = [o for o in pool
               if not heeft_tag(o, "patroon", "pers", "press", "overhead", "front")
               and "front raise" not in _lc(o.get("naam"))]
        sub = sub or pool
        # Stubborn-regel: laterale delts krijgen geen pers-spillover op de zijkant.
        # Het EERSTE schouder-slot van de week is daarom altijd een abductie
        # (lateral raise); rear-delt-werk komt via latere slots en het prehab-slot.
        if not any("abductie" in p for p in week_patronen["Schouders"]):
            lat = [o for o in sub if heeft_tag(o, "patroon", "abductie")]
            return lat or sub
        return sub
    if spier == "Rug":
        # Balans i.p.v. alleen aanwezigheid: prefereer het ONDERVERTEGENWOORDIGDE
        # trekpatroon (anders kan een week op 7x verticaal / 2x horizontaal eindigen).
        n_vert = sum(1 for p in week_patronen["Rug"] if "vert" in p)
        n_hor = sum(1 for p in week_patronen["Rug"] if "hor" in p)
        if n_vert > n_hor:
            sub = [o for o in pool if heeft_tag(o, "patroon", "hor")]
            return sub or pool
        if n_hor > n_vert:
            sub = [o for o in pool if heeft_tag(o, "patroon", "vert")]
            return sub or pool
    if spier == "Quads" and dag_type in ("LOWER", "FULL"):
        bilat_squat = any("squat" in p and "|uni" not in p
                          for p in week_patronen["Quads"])
        if not bilat_squat:
            sub = [o for o in pool if heeft_tag(o, "patroon", "squat", "knie")]
            return sub or pool
        # BESLUIT 12 juni (Bas): max 1 bilaterale squat-variant per week — twee
        # squat-machines naast elkaar is overkill. Vervolg-slots: leg extension
        # of unilateraal werk (single-leg press, lunge).
        sub = [o for o in pool if heeft_tag(o, "patroon", "knie") or is_unilateraal(o)]
        return sub or pool
    if spier == "Hams" and dag_type in ("LOWER", "LEGS"):
        heeft_hinge = any("hinge" in p or "heup" in p for p in week_patronen["Hams"])
        if not heeft_hinge:
            sub = [o for o in pool if heeft_tag(o, "patroon", "hinge", "heup", "deadlift")]
            return sub or pool
    return pool


def kies_oefening(pool, klantnaam, spier, slot_id, cyclus, gebruikt, compound_eerst):
    """SOP par.8 lagen 3-5: rotatie, coach-bias 2-van-3, deterministische seed."""
    if not pool:
        return None
    kandidaten = [o for o in pool if o.get("naam") not in gebruikt] or pool
    if compound_eerst:
        comp = [o for o in kandidaten if _lc(o.get("type")) == "compound"]
        if comp:
            kandidaten = comp
    variatie_cyclus = (cyclus % 3 == 0)
    def tier(o):
        p = _lc(o.get("coach_prioriteit"))
        if "vermijden" in p:
            return 9   # laatste redmiddel: alleen kiezen als er niets anders is
        if "voorkeur" in p:
            return 1 if variatie_cyclus else 0
        if "nodig" in p:
            return 2
        return 0 if variatie_cyclus else 1
    beste_tier = min(tier(o) for o in kandidaten)
    top = sorted([o for o in kandidaten if tier(o) == beste_tier],
                 key=lambda o: _lc(o.get("naam")))
    idx = seed_int(klantnaam, spier, slot_id, cyclus) % len(top)
    return top[idx]


def patroon_familie(oef):
    """Bewegingsfamilie voor de sessie-regel: alle squat-achtige patronen (Squat,
    Squat-press) vormen EEN familie; overige patronen zijn hun eigen familie.
    Zo mag incline-pers naast vlakke pers (andere borstregio), en row naast
    pulldown — maar Leg Press niet naast Hack Squat."""
    p = _lc(oef.get("patroon"))
    return "squat" if "squat" in p else p


def koppel_arm_supersets(volgorde):
    """BESLUIT 12 juni (Bas): supersets ALLEEN voor armen (tijdwinst), nooit voor
    compounds of andere spieren. Koppelt een biceps- en triceps-isolatie in
    dezelfde sessie tot een superset-paar (veld 'superset': 'A'), en zet ze
    direct naast elkaar. Meta-analyse: agonist-antagonist supersets behouden
    volume en adaptatie bij kortere sessieduur."""
    def is_arm_iso(it):
        oef = it["oefening"]
        return (oef.get("primaire_spier") in ("Biceps", "Triceps")
                and _lc(oef.get("type")) != "compound" and not it.get("prehab"))
    bi = [i for i, it in enumerate(volgorde)
          if is_arm_iso(it) and it["oefening"]["primaire_spier"] == "Biceps"]
    tri = [i for i, it in enumerate(volgorde)
           if is_arm_iso(it) and it["oefening"]["primaire_spier"] == "Triceps"]
    label = "A"
    for b_i, t_i in zip(bi, tri):
        volgorde[b_i]["superset"] = label
        volgorde[t_i]["superset"] = label
        label = chr(ord(label) + 1)
    # paren naast elkaar zetten (tri direct na zijn bi-partner)
    for b_i, t_i in zip(bi, tri):
        it = volgorde[t_i]
        b_pos = volgorde.index(volgorde[b_i])
        volgorde.remove(it)
        volgorde.insert(volgorde.index([x for x in volgorde
                        if x.get("superset") == it.get("superset")][0]) + 1, it)
    return volgorde


# ---- SOP v3.3 par.8-V: volgorde-laag (gelockt 12 juni 2026) ----
V_PERS_PATRONEN = ("horizontale pers", "incline pers", "verticale pers", "dip")
V_TREK_PATRONEN = ("verticale trek", "horizontale trek")
V_GUARDRAIL_PATRONEN = ("squat", "squat-press", "hinge")
V_PERS_KANT = ("Borst", "Schouders", "Triceps")
V_TREK_KANT = ("Rug", "Biceps")
V_BEEN = ("Quads", "Hams", "Billen")


def _v_kant(spier):
    if spier in V_PERS_KANT:
        return "pers"
    if spier in V_TREK_KANT:
        return "trek"
    if spier in V_BEEN:
        return "been"
    return "overig"


def _v_is_pers_compound(it):
    o = it["oefening"]
    return _lc(o.get("type")) == "compound" and _lc(o.get("patroon")) in V_PERS_PATRONEN


def _v_is_trek_compound(it):
    o = it["oefening"]
    return _lc(o.get("type")) == "compound" and _lc(o.get("patroon")) in V_TREK_PATRONEN


def _v_is_arm_iso(it):
    o = it["oefening"]
    return (o.get("primaire_spier") in ("Biceps", "Triceps")
            and _lc(o.get("type")) != "compound" and not it.get("prehab"))


def orden_sessie(items, voorkeur, cyclus=1, dag_type="FULL", flags=None):
    """SOP v3.3 par.8-V (herzien 12 juni 2026 — harde blokvolgorde):
    BLOKVOLGORDE (hard): grote compounds (borst/rug/benen) -> schouders -> armen
        -> accessoires (kuiten/onderrug/prehab) -> core. Geldt voor ALLE schouder-
        werk, ook losse delt-isolaties: nooit een arm voor een schouder.
    V-1 opener: voorkeurspier altijd; anders rotatie per cyclus (c1 rug, c2 borst).
    V-2 FULL/LOWER: squat/hinge-compound op slot <=3 indien aanwezig (geen verplichting).
    V-3 synergist HARD: binnen het hoofdblok geen arm-isolatie -> al afgevangen
        doordat armen een eigen, later blok zijn.
    V-4 push-pull interleave BINNEN elk blok (borst<->rug, biceps<->triceps)."""
    flags = flags if flags is not None else []

    def _flag(f):
        if f not in flags:
            flags.append(f)

    ARM = ("Biceps", "Triceps")
    SCHOUDER = ("Schouders",)

    hoofd, schouder, arm, acc, core = [], [], [], [], []
    for it in items:
        sp = it["oefening"].get("primaire_spier")
        if it.get("prehab") or sp in ("Kuiten", "Onderrug", "Adductoren"):
            acc.append(it)            # accessoires/prehab apart, ongeacht spier
        elif sp == "Core":
            core.append(it)
        elif sp in ARM:
            arm.append(it)
        elif sp in SCHOUDER:
            schouder.append(it)
        else:
            hoofd.append(it)          # borst/rug/benen-blok (de grote compounds)

    def _interleave(groep_items, kant_a, kant_b, opener_groep=None):
        """Push-pull interleave binnen een blok. Per spiergroep compounds eerst.
        Optioneel forceert opener_groep de eerste positie."""
        per_spier = {}
        for it in groep_items:
            per_spier.setdefault(it["oefening"].get("primaire_spier"), []).append(it)
        for g in per_spier:
            per_spier[g].sort(key=lambda x: 0 if _lc(x["oefening"].get("type")) == "compound" else 1)
        groepen_a = sorted(g for g in per_spier if g in kant_a)
        groepen_b = sorted(g for g in per_spier if g in kant_b)
        rest = sorted(g for g in per_spier if g not in kant_a and g not in kant_b)
        # opener vooraan plaatsen
        startlijst = groepen_a
        if opener_groep:
            for bucket in (groepen_a, groepen_b, rest):
                if opener_groep in bucket:
                    bucket.remove(opener_groep)
            if opener_groep in kant_b:
                groepen_b.insert(0, opener_groep); a, b = groepen_b, groepen_a
            else:
                groepen_a.insert(0, opener_groep); a, b = groepen_a, groepen_b
        else:
            a, b = groepen_a, groepen_b
        # round-robin per ronde, push-pull afgewisseld
        uit = []
        r = 0
        volg_g = []
        # bouw afwisselende groepsvolgorde
        ga, gb = list(a), list(b)
        while ga or gb:
            if ga: volg_g.append(ga.pop(0))
            if gb: volg_g.append(gb.pop(0))
        volg_g += rest
        while any(len(per_spier[g]) > r for g in volg_g):
            for g in volg_g:
                if len(per_spier[g]) > r:
                    uit.append(per_spier[g][r])
            r += 1
            if r > 20:
                break
        return uit

    # ---- BLOK 1: grote compounds (borst/rug/benen), push-pull interleave ----
    PERS_GROEP = ("Borst",)
    TREK_GROEP = ("Rug",)
    aanwezig = {it["oefening"].get("primaire_spier") for it in hoofd}
    # V-1 opener bepalen
    opener = None
    if voorkeur and voorkeur in aanwezig:
        opener = voorkeur
    elif dag_type in ("LOWER", "LEGS"):
        opener = next((g for g in ("Quads", "Hams", "Billen") if g in aanwezig), None)
    elif aanwezig & set(PERS_GROEP + TREK_GROEP):
        eerste, tweede = ("Rug", "Borst") if cyclus % 2 == 1 else ("Borst", "Rug")
        opener = eerste if eerste in aanwezig else (tweede if tweede in aanwezig else None)
        if opener:
            _flag("OPENER_ROTATIE_" + opener.upper())

    blok1 = _interleave(hoofd, PERS_GROEP, TREK_GROEP, opener_groep=opener)

    # V-2 guardrail binnen blok 1 (FULL/LOWER): squat/hinge-compound op slot <=3
    if dag_type in BEEN_DAGTYPES:
        def is_been_comp(x):
            o = x["oefening"]
            return (_lc(o.get("type")) == "compound"
                    and _lc(o.get("patroon")) in V_GUARDRAIL_PATRONEN)
        idx = next((i for i, x in enumerate(blok1) if is_been_comp(x)), None)
        if idx is None:
            if dag_type in ("LOWER", "LEGS"):
                _flag("GUARDRAIL_LOWER_ZONDER_SQUAT_HINGE")
        elif idx > 2:
            blok1.insert(2, blok1.pop(idx))
            _flag("GUARDRAIL_SLOT3_GEREPAREERD")

    # ---- BLOK 2: schouders ----
    blok2 = _interleave(schouder, SCHOUDER, ())

    # ---- BLOK 3: armen, push-pull interleave (biceps<->triceps) ----
    blok3 = _interleave(arm, ("Biceps",), ("Triceps",))

    # samenvoegen: compounds -> schouders -> armen -> accessoires -> core
    return blok1 + blok2 + blok3 + acc + core


def _orden_sessie_OUD(items, voorkeur, cyclus=1, dag_type="FULL", flags=None):
    """GEDEPRECEerd — vervangen door de harde blokvolgorde hierboven (12 juni)."""
    flags = flags if flags is not None else []

    def _flag(f):
        if f not in flags:
            flags.append(f)

    hoofd, acc, core = [], [], []
    for it in items:
        sp = it["oefening"].get("primaire_spier")
        if sp == "Core":
            core.append(it)
        elif sp in ("Kuiten", "Onderrug") or it.get("prehab"):
            acc.append(it)
        else:
            hoofd.append(it)
    groepen = {}
    for it in hoofd:
        groepen.setdefault(it["oefening"].get("primaire_spier"), []).append(it)
    for g in groepen:
        groepen[g].sort(key=lambda x: 0 if _lc(x["oefening"].get("type")) == "compound" else 1)
    if not groepen:
        return hoofd + acc + core

    # V-1 opener
    aanwezig = set(groepen)
    if voorkeur and voorkeur in aanwezig:
        opener = voorkeur
    elif dag_type in ("LOWER", "LEGS"):
        opener = next((g for g in ("Quads", "Hams", "Billen") if g in aanwezig),
                      sorted(aanwezig)[0])
    else:
        eerste, tweede = ("Rug", "Borst") if cyclus % 2 == 1 else ("Borst", "Rug")
        opener = eerste if eerste in aanwezig else (
            tweede if tweede in aanwezig else sorted(aanwezig)[0])
        _flag("OPENER_ROTATIE_" + opener.upper())

    # V-4 groepsvolgorde: opener, afwisselend pers/trek (compound-groepen),
    # benen vroeg (guardrail haalbaar); isolatie-only groepen daarna.
    def heeft_comp(g):
        return any(_lc(x["oefening"].get("type")) == "compound" for x in groepen[g])
    rest = [g for g in groepen if g != opener]
    comp_g = [g for g in rest if heeft_comp(g)]
    iso_g = [g for g in rest if not heeft_comp(g)]
    pers = sorted(g for g in comp_g if _v_kant(g) == "pers")
    trek = sorted(g for g in comp_g if _v_kant(g) == "trek")
    been = sorted(g for g in comp_g if _v_kant(g) == "been")
    ovr = sorted(g for g in comp_g if _v_kant(g) == "overig")
    volg_g = [opener]
    if been:
        volg_g.append(been.pop(0))
    a, b = (trek, pers) if _v_kant(opener) == "pers" else (pers, trek)
    while a or b or been:
        if a: volg_g.append(a.pop(0))
        if been: volg_g.append(been.pop(0))
        if b: volg_g.append(b.pop(0))
    volg_g += ovr
    ib = sorted(g for g in iso_g if _v_kant(g) == "been")
    ip = sorted(g for g in iso_g if _v_kant(g) == "pers")
    itk = sorted(g for g in iso_g if _v_kant(g) == "trek")
    io = sorted(g for g in iso_g if g not in ib + ip + itk)
    volg_g += ib
    a, b = (itk, ip) if _v_kant(opener) == "pers" else (ip, itk)
    while a or b:
        if a: volg_g.append(a.pop(0))
        if b: volg_g.append(b.pop(0))
    volg_g += io

    # V-0 rondes
    volgorde = []
    r = 0
    while any(len(groepen[g]) > r for g in volg_g):
        for g in volg_g:
            if len(groepen[g]) > r:
                volgorde.append(groepen[g][r])
        r += 1
        if r > 20:
            break

    # V-2 guardrail (FULL/LOWER): ALS er een squat/hinge-compound is, staat die
    # uiterlijk op slot 3. De guardrail dwingt GEEN squat af die er niet is — de
    # weekelijkse bilaterale-squat-cap mag een FB-dag legitiem zonder squat-compound
    # laten (besluit Bas 12 juni: ordening-regel, geen verplichting). Ontbreekt er
    # een squat/hinge én is het een LOWER-dag, dan is dat wél onverwacht -> info-flag.
    if dag_type in BEEN_DAGTYPES:
        def is_been_comp(x):
            o = x["oefening"]
            return (_lc(o.get("type")) == "compound"
                    and _lc(o.get("patroon")) in V_GUARDRAIL_PATRONEN)
        idx = next((i for i, x in enumerate(volgorde) if is_been_comp(x)), None)
        if idx is None:
            if dag_type in ("LOWER", "LEGS"):
                _flag("GUARDRAIL_LOWER_ZONDER_SQUAT_HINGE")
        elif idx > 2:
            volgorde.insert(2, volgorde.pop(idx))
            _flag("GUARDRAIL_SLOT3_GEREPAREERD")

    # V-3 synergist-bescherming (hard, fixpoint-reparatie)
    for _ in range(10):
        lp = max((i for i, x in enumerate(volgorde) if _v_is_pers_compound(x)), default=-1)
        lt = max((i for i, x in enumerate(volgorde) if _v_is_trek_compound(x)), default=-1)
        schend = next((i for i, x in enumerate(volgorde) if _v_is_arm_iso(x) and (
            (x["oefening"].get("primaire_spier") == "Triceps" and i < lp)
            or (x["oefening"].get("primaire_spier") == "Biceps" and i < lt))), None)
        if schend is None:
            break
        doel = lp if volgorde[schend]["oefening"].get("primaire_spier") == "Triceps" else lt
        volgorde.insert(doel, volgorde.pop(schend))
        _flag("SYNERGIST_GEREPAREERD")

    return volgorde + acc + core


# ----------------------------- B6: VOORSCHRIFT (SOP v3.2 par.9) -------------

# DEFINITIEF (SOP v3.2 par.9, verbatim SOP v1 B6; overhaul: "ongewijzigd").
# Rep-ranges per categorie per krachtniveau + rust. Categorie-bepaling gebruikt
# beschikbare tags; mapping geverifieerd zodra bibliotheek v1.4 terug is.
B6_REPS = {
    # categorie: {BEG, INT, ADV}
    "heavy_compound":    {"BEG": None,    "INT": "5-8",   "ADV": "4-6"},
    "standard_compound": {"BEG": "8-12",  "INT": "6-10",  "ADV": "5-8"},
    "iso_stretch":       {"BEG": "10-15", "INT": "8-12",  "ADV": "6-10"},
    "iso_peak":          {"BEG": "10-15", "INT": "10-15", "ADV": "8-12"},
    "lateral_raise":     {"BEG": "12-15", "INT": "12-15", "ADV": "10-12"},
    "kuit_gastroc":      {"BEG": "10-15", "INT": "8-12",  "ADV": "6-10"},
    "kuit_soleus":       {"BEG": "15-20", "INT": "12-20", "ADV": "10-15"},
    "core_dyn":          {"BEG": "10-15", "INT": "10-15", "ADV": "10-15"},
    "core_iso":          {"BEG": "30-60s", "INT": "45-75s", "ADV": "60-90s"},
}
B6_RUST = {
    "heavy_compound": "2.5-3 min", "standard_compound": "2 min",
    "iso_groot": "90-120 s", "iso_klein": "60-90 s",
    "kuit": "60-90 s", "core": "45-60 s",
}
GROTE_SPIEREN = ("Borst", "Rug", "Quads", "Hams", "Billen")


def b6_categorie(oef):
    naam = _lc(oef.get("naam"))
    spier = oef.get("primaire_spier")
    if spier == "Kuiten":
        return "kuit_soleus" if "seated" in naam or "zit" in naam else "kuit_gastroc"
    if spier == "Core":
        return "core_iso" if any(t in naam for t in ("plank", "hold", "pallof")) else "core_dyn"
    if "lateral raise" in naam:
        return "lateral_raise"
    if _lc(oef.get("type")) == "compound":
        return "heavy_compound" if is_big3(oef) else "standard_compound"
    # isolatie: stretch- vs peak-profiel via weerstandsprofiel-tag (bibliotheek v1.4)
    if "gerekt" in _lc(oef.get("weerstandsprofiel")):
        return "iso_stretch"
    return "iso_peak"


def schrijf_voor(oef, kracht):
    """SOP v3.2 par.9: reps + rust per categorie per krachtniveau."""
    cat = b6_categorie(oef)
    reps = B6_REPS[cat][kracht]
    if reps is None:  # heavy compound bij BEG: skill cap -> standaard-compound-bereik
        reps = B6_REPS["standard_compound"]["BEG"]
    if cat == "heavy_compound":
        rust = B6_RUST["heavy_compound"]
    elif cat == "standard_compound":
        rust = B6_RUST["standard_compound"]
    elif cat.startswith("kuit"):
        rust = B6_RUST["kuit"]
    elif cat.startswith("core"):
        rust = B6_RUST["core"]
    elif oef.get("primaire_spier") in GROTE_SPIEREN:
        rust = B6_RUST["iso_groot"]
    else:
        rust = B6_RUST["iso_klein"]
    return reps, rust

# ----------------------------- HOOFDPIJPLIJN --------------------------------

def normaliseer_fb_dagen(per_dag, template, cyclus, dag_cap):
    """TAAK F (15 juni): maak Full Body-dagen lean en professioneel.
    - F2/F3: schouders max 2 sets (1 oefening) per FB-dag.
    - F4: armen biceps 2 + triceps 2 op ELKE FB-dag.
    - F5: max 1 accessoire per FB-dag, roterend per cyclus + dagindex.
    Werkt cap-bewust: armen + schouder(2) zijn beschermd; bij cap-overschrijding wordt
    eerst het roterende accessoire teruggetrimd.
    """
    ACC_ROT = ["Core", "Kuiten", "Onderrug"]      # roterende FB-accessoire-pool
    ALLE_ACC = ("Core", "Kuiten", "Onderrug", "Adductoren")
    fb_idx = [j for j, (_, t) in enumerate(template) if t == "FULL"]
    for k, j in enumerate(fb_idx):
        dag = per_dag[j]
        # F2/F3: schouders cap 2
        if dag.get("Schouders", 0) > 2:
            dag["Schouders"] = 2
        # F4: armen exact 2+2
        dag["Biceps"] = 2
        dag["Triceps"] = 2
        # F5: kies 1 roterend accessoire, verwijder de rest
        gekozen = ACC_ROT[(cyclus - 1 + k) % len(ACC_ROT)]
        for acc in ALLE_ACC:
            if acc == gekozen:
                dag[acc] = max(dag.get(acc, 0), 2)
            else:
                dag.pop(acc, None)
        # cap-bewust: bij overschrijding eerst het accessoire terugtrimmen (nooit onder 0),
        # compounds/armen/schouder(2) blijven beschermd.
        overschot = sum(dag.values()) - dag_cap
        if overschot > 0 and dag.get(gekozen, 0) > 0:
            af = min(overschot, dag[gekozen])
            dag[gekozen] -= af
            if dag[gekozen] < 2:           # geen 1-set splinter
                dag.pop(gekozen, None)
    return per_dag


def genereer(bib, intake, cyclus):
    flags = []
    naam = intake.get("naam", "onbekend")
    kracht, ervaring, eff_ervaring, re_entry = classificeer(intake, flags)
    dagen = int(intake.get("dagen", 3))
    minuten = int(intake.get("minuten", 60))
    voorkeur = intake.get("voorkeurspier") or None
    cap = sessie_cap(minuten, intake.get("geslacht", "M"), kracht)
    weekbudget = dagen * cap  # tijd-budget; landmarks bepalen het volume, dit is de plafond-check
    # BESLUIT 11 juni #6: cyclusfocus via coach-logica (synergie + anticipatie),
    # geen seed-willekeur. Zie focus_sequentie() voor de regels.
    seq = focus_sequentie(voorkeur, re_entry)
    focus = seq[(cyclus - 1) % len(seq)]
    focus_accessoire = FOCUS_SPIER.get(focus)  # None bij houding/grip
    rationale = focus_rationale(focus, voorkeur, re_entry, cyclus)
    volume, accessoire, diag = verdeel_volume(weekbudget, voorkeur, kracht, flags,
                                              focus_accessoire=focus_accessoire,
                                              houding_focus=(focus == "houding"),
                                              geslacht=intake.get("geslacht", "M"),
                                              ervaring=eff_ervaring)
    if re_entry and cyclus == 1 and RE_ENTRY_VOLUME[kracht] < 1.0:
        f = RE_ENTRY_VOLUME[kracht]
        volume = {m: max(2, int(round(v * f))) for m, v in volume.items()}
    template = split_template(dagen)
    dag_types = [t for _, t in template]
    if dagen >= 6:
        flags.append("MANUAL_SPLIT_6PLUS")  # SOP par.2: 6+ dagen vereist coach-review
    # Iteratief: plannen -> plaatsen -> past het niet, dan WEEK-volume knippen via de
    # besloten hierarchie en herplaatsen (max 4 rondes). Garandeert: wat in het schema
    # staat, past in de tijd, en tijdgebrek raakt nooit stiekem core/armen.
    dag_capaciteit = max(8, cap - 2)
    for _ronde in range(4):
        alle_volume = dict(volume)
        alle_volume.update(accessoire)
        per_dag, onplaatsbaar = verdeel_over_dagen(alle_volume, dag_types,
                                                   dag_cap=dag_capaciteit)
        if onplaatsbaar <= 0:
            break
        flags.append(f"HERPLAATSING_RONDE_TEKORT_{onplaatsbaar}")
        rest = knip_volume(volume, accessoire, onplaatsbaar, kracht,
                           focus_accessoire, flags)
        if rest > 0:
            break  # beschermde floors bereikt; laatste plaatsing geldt

    # ---- OPVUL-MECHANISME (besluit Bas 12 juni): vul LICHTE dagen aan tot een
    # redelijk niveau met accessoires, zodat trainingstijd niet wordt verspild.
    # AFREGELING: vul tot het niveau van de zwaarste 'echte' dag (begrensd op ~85%
    # cap), maar NOOIT een dag oppompen die al zwaar is, en niet boven de cap. ----
    dag_totalen = [sum(p.values()) for p in per_dag]
    zwaarste = max(dag_totalen) if dag_totalen else 0
    FILL_DOEL = min(int(round(0.85 * dag_capaciteit)), zwaarste)
    FILL_POOLS = {
        # F1 (15 juni): Billen verwijderd uit alle fill-pools. Mannen krijgen geen losse
        # bil-fill meer; bilwerk loopt via squat/hinge-spillover + de 45° back extension
        # (Onderrug-primair). Vrouwen krijgen billen als PRIMAIRE spier (taak A), niet via fill.
        "LOWER": [("Kuiten", 2), ("Onderrug", 2)],
        "LEGS":  [("Kuiten", 2), ("Onderrug", 2)],
        "UPPER": [("Schouders", 2), ("Core", 2)],     # rear-delt/houding + core
        "PUSH":  [("Schouders", 2), ("Core", 2)],
        "PULL":  [("Core", 2), ("Onderrug", 2)],
        "FULL":  [("Core", 2)],
    }
    FILL_WEEK_CAP = {"Kuiten": 6, "Onderrug": 4, "Schouders": 4, "Core": 6}
    fill_week = defaultdict(int)
    for j, t in enumerate(dag_types):
        huidig = sum(per_dag[j].values())
        # sla dagen over die al >=80% van het fill-doel zitten: niet verder oppompen
        if huidig >= FILL_DOEL - 1:
            continue
        for spier, blok in FILL_POOLS.get(t, []):
            if huidig >= FILL_DOEL:
                break
            reeds = sum(per_dag[k].get(spier, 0) for k in range(len(dag_types)))
            if reeds + blok > FILL_WEEK_CAP.get(spier, 6):
                continue
            if huidig + blok > FILL_DOEL:
                blok = FILL_DOEL - huidig
            if blok < 2:
                continue
            per_dag[j][spier] = per_dag[j].get(spier, 0) + blok
            fill_week[spier] += blok
            huidig += blok
    if fill_week:
        flags.append("OPVUL_ACCESSOIRES_" + "_".join(f"{k}{v}" for k, v in fill_week.items()))

    # TAAK F (15 juni): Full Body-dagen normaliseren (lean schema, armen elke FB-dag,
    # 1 roterend accessoire, schouders max 2). Na fill, vóór de selectielus.
    per_dag = normaliseer_fb_dagen(per_dag, template, cyclus, dag_capaciteit)

    week_patronen = defaultdict(list)
    gebruikt_week = set()
    gebruikt_groepen = set()  # substitutiegroepen (max 1 per groep per week)
    sessies = []
    prehab_dag = seed_int(naam, "prehab", cyclus) % len(template)
    # TAAK F (15 juni): prehab-slot NIET op een Full Body-dag — die blijft lean met 1
    # roterend accessoire (geen 2e schouder/accessoire erbij). Verschuif naar een niet-FB-dag
    # indien beschikbaar; bij een pure FB-klant (alle dagen FULL) vervalt het prehab-slot.
    _niet_fb = [i for i, (_, t) in enumerate(template) if t != "FULL"]
    if template[prehab_dag][1] == "FULL" and _niet_fb:
        prehab_dag = _niet_fb[seed_int(naam, "prehab", cyclus) % len(_niet_fb)]

    for d, (dag_naam, dag_type) in enumerate(template):
        items = []
        gebruikt_dag = set()  # FIX 12 juni: geen dubbele oefening binnen EEN sessie
        dag_bilat_compound = set()  # (spier, patroon_familie) van bilaterale compounds deze sessie
        for spier, sets_dag in sorted(per_dag[d].items(),
                                      key=lambda kv: -kv[1]):
            if sets_dag <= 0:
                continue
            n_oef = 1 if sets_dag <= 3 else 2
            # FIX 12 juni: tel hoeveel DISTINCTE oefeningen er deze sessie nog
            # beschikbaar zijn voor deze spier (na ALLE week-caps incl. de bilaterale
            # squat-familie-cap). Zijn dat er minder dan de geplande slots, dan slots
            # samenvouwen i.p.v. dezelfde oefening herhalen (Owen-FB Leg Extension-bug).
            # NB: gebruikt_week NIET uitsluiten — isolaties mogen over dagen herhalen,
            # alleen niet binnen EEN sessie (gebruikt_dag).
            _pool_check = harde_filters(bib, spier, intake, eff_ervaring, cyclus)
            _pool_check = structuur_filter(_pool_check, spier, dag_type, week_patronen)
            _distinct = len({o.get("naam") for o in _pool_check
                             if o.get("naam") not in gebruikt_dag})
            if spier == "Schouders":
                # F2 (15 juni): max 2 sets per schouderoefening -> chunks van 2.
                n_oef = max(1, (sets_dag + 1) // 2)        # ceil(sets/2)
                if _distinct >= 1:
                    n_oef = min(n_oef, _distinct)
                verdeling, rest = [], sets_dag
                for _ in range(n_oef):
                    take = min(2, rest); verdeling.append(take); rest -= take
                # geen 1-set splinter: trailing 1 valt weg (max 2/oefening blijft heilig)
                verdeling = [v for v in verdeling if v >= 2] or [min(2, sets_dag)]
            else:
                n_oef = 1 if sets_dag <= 3 else 2
                if _distinct >= 1:
                    n_oef = min(n_oef, _distinct)
                verdeling = [sets_dag] if n_oef == 1 else \
                    [sets_dag - sets_dag // 2, sets_dag // 2]
            for s_i, n_sets in enumerate(verdeling):
                pool = harde_filters(bib, spier, intake, eff_ervaring, cyclus)
                pool = structuur_filter(pool, spier, dag_type, week_patronen)
                # BESLUIT 12 juni: max 1 oefening per substitutiegroep per week —
                # voorkomt 2x dezelfde regio/variant (2 incline-persen, 2 squat-
                # machines, 2 flies). Soft: valt terug op de volle pool indien leeg.
                # BESLUIT 12 juni (Bas, verduidelijkt) — HARDE sessie-regel, gaat
                # vóór de zachte groep-voorkeur: max 1 bilaterale compound per
                # SPIER + BEWEGINGSFAMILIE per sessie. Meerdere compounds per dag
                # mag dus, mits ze anders targetten: incline- naast vlakke pers,
                # row naast pulldown, squat naast hinge — maar NIET Leg Press
                # naast Hack Squat (zelfde spier, zelfde squat-familie).
                verboden_fam = {fam for (sp, fam) in dag_bilat_compound if sp == spier}
                if verboden_fam:
                    pool_ok = [o for o in pool
                               if _lc(o.get("type")) != "compound"
                               or is_unilateraal(o)
                               or patroon_familie(o) not in verboden_fam]
                    if pool_ok:
                        pool = pool_ok
                    else:
                        flags.append(f"GEEN_ALTERNATIEF_BESCHIKBAAR_{spier}")
                pool_g = [o for o in pool
                          if _lc(o.get("substitutiegroep")) not in gebruikt_groepen]
                pool = pool_g or pool
                # FIX 12 juni: nooit dezelfde oefening 2x in EEN sessie (Leg Extension-bug).
                pool_d = [o for o in pool if o.get("naam") not in gebruikt_dag]
                pool = pool_d or pool
                # BESLUIT 12 juni (Bas): bij lage frequentie (<=2 dagen, full body)
                # compound-dominant programmeren — compounds dekken meer bij weinig
                # sessies. ALLE slots van de grote vier krijgen dan compound-
                # voorkeur; isolaties verschijnen alleen waar de harde regels
                # compounds blokkeren (bv. quads-vervolgslot -> leg extension via
                # de 1-bilaterale-squat-per-week-regel). Schouders/core/kuiten/
                # onderrug/armen behouden hun eigen beleid.
                lage_freq = dagen <= 2
                compound_eerst = ((s_i == 0 or lage_freq)
                                  and spier in ("Borst", "Rug", "Quads", "Hams"))
                # FIX 12 juni: op FULL/LOWER moet het eerste been-slot een squat/hinge-
                # compound krijgen als die nog beschikbaar is — anders mist de guardrail
                # zijn anker (Owen-FB had 3x Leg Extension, nul squat). Dwingt compound
                # af zelfs als de week-rotatie de voorkeurscompound al verbruikte.
                if (s_i == 0 and dag_type in BEEN_DAGTYPES
                        and spier in ("Quads", "Hams")):
                    comp_beschikbaar = [o for o in pool
                                        if _lc(o.get("type")) == "compound"]
                    if comp_beschikbaar:
                        pool = comp_beschikbaar
                        compound_eerst = True
                # FIX 12 juni (Bas): hamstring krijgt bij >=2 slots een CURL (knieflexie)
                # naast de hinge — symmetrisch met quads (compound + leg extension).
                # Zodra een hinge gekozen is, stuurt het vervolg-slot naar een curl.
                if (s_i > 0 and spier == "Hams"):
                    al_hinge = any(("hinge" in p or "heup" in p or "deadlift" in p)
                                   for p in week_patronen["Hams"])
                    if al_hinge:
                        curls = [o for o in pool
                                 if _lc(o.get("patroon")) == "knieflexie"
                                 and o.get("naam") not in gebruikt_dag]
                        if curls:
                            pool = curls
                            compound_eerst = False
                oef = kies_oefening(pool, naam, spier, f"{d}-{s_i}", cyclus,
                                    gebruikt_week, compound_eerst)
                if oef is None:
                    flags.append(f"GEEN_OEFENING_{spier}")
                    continue
                gebruikt_week.add(oef.get("naam"))
                gebruikt_dag.add(oef.get("naam"))
                gebruikt_groepen.add(_lc(oef.get("substitutiegroep")))
                week_patronen[spier].append(
                    _lc(oef.get("patroon")) + ("|uni" if is_unilateraal(oef) else ""))
                if _lc(oef.get("type")) == "compound" and not is_unilateraal(oef):
                    dag_bilat_compound.add((spier, patroon_familie(oef)))
                items.append({"oefening": oef, "sets": n_sets, "prehab": False})
        if d == prehab_dag and dag_type != "FULL":
            # SOP par.12: roterend prehab-slot (lage rug / houding / grip).
            # FIX 10 juni: lage rug overslaan als Onderrug al accessoirevolume krijgt
            # (anders 5 sets onderrug/wk + dubbele oefening — gevonden in testrun).
            PREHAB_POOLS = [
                ("houding", lambda o: _lc(o.get("patroon")).startswith("horizontale trek (hoog)")),
                ("grip", lambda o: "hammer" in _lc(o.get("naam")) or "carry" in _lc(o.get("naam"))),
                ("lage_rug", lambda o: o.get("primaire_spier") == "Onderrug"),
            ]
            cats = [c for c in PREHAB_POOLS
                    if not (c[0] == "lage_rug" and accessoire.get("Onderrug", 0) > 0)]
            # FOCUS-GESTUURD (besluit #6): grip-focus -> grip-prehab; alle andere
            # cycli -> houding/rear-delt eerst (universeel waardevol bij zittend
            # publiek, en de zichtbare kern van een houding-focuscyclus).
            volgorde_namen = ["grip", "houding", "lage_rug"] if focus == "grip" \
                else ["houding", "grip", "lage_rug"]
            cats.sort(key=lambda c: volgorde_namen.index(c[0]))
            oef = None
            for k in range(len(cats)):
                _, past = cats[k]
                pool = [o for o in bib if past(o)
                        and o.get("naam") not in gebruikt_week]
                pool = [o for o in pool
                        if ERVARING_RANG.get(o.get("techniek_niveau", "Expert"), 2)
                        <= ERVARING_RANG[eff_ervaring]
                        and materiaal_ok(o, intake)]
                if pool:
                    oef = sorted(pool, key=lambda o: _lc(o.get("naam")))[
                        seed_int(naam, "prehab", cyclus) % len(pool)]
                    break
            if oef is not None:
                gebruikt_week.add(oef.get("naam"))
                items.append({"oefening": oef, "sets": PREHAB_SETS, "prehab": True})

        # big3-straf + unilaterale tijd: trim isolaties als de sessie over de cap gaat
        def kost(it):
            o = it["oefening"]
            per_set = UNILATERAAL_TIJD if is_unilateraal(o) else 1.0
            return it["sets"] * per_set + (BIG3_STRAF if is_big3(o) else 0)
        totaal = sum(kost(it) for it in items)
        while totaal > cap:
            iso = [it for it in items
                   if _lc(it["oefening"].get("type")) != "compound" and not it["prehab"]]
            # FIX 11 juni: nooit naar 1 set knippen (geen junk-sets). Trim-volgorde:
            # 1) isolaties met >=3 sets; 2) anders een 2-set isolatie schrappen.
            # BESCHERMING (besluit #1): stubborn muscles (armen) worden ALS LAATSTE
            # geraakt — hun hoge spillover mag ze niet bovenaan de schraplijst zetten.
            def trim_prio(it):
                sp = it["oefening"].get("primaire_spier")
                beschermd = 1 if sp in DIRECT_DOEL_HARD else 0
                return (beschermd, -SPILLOVER.get(sp, 0), -it["sets"])
            drie = [it for it in iso if it["sets"] >= 3]
            if drie:
                kies = min(drie, key=trim_prio)  # hoogste spillover, onbeschermd, eerst
                kies["sets"] -= 1
            else:
                # Core is hard beschermd: mag nooit volledig geschrapt worden
                # (besluit: core komt ALTIJD elke week voor).
                # Core en armen (DIRECT_DOEL_HARD) zijn hard beschermd tegen
                # volledig schrappen — die floors gelden ook binnen de sessie-trim.
                twee = [it for it in iso if it["sets"] == 2
                        and it["oefening"].get("primaire_spier") != "Core"
                        and it["oefening"].get("primaire_spier") not in DIRECT_DOEL_HARD]
                # Stubborn-bescherming: abductie (laterale delts) pas schrappen als
                # er echt niets anders meer is (zelfde filosofie als armen/kuiten).
                niet_lat = [it for it in twee
                            if not heeft_tag(it["oefening"], "patroon", "abductie")]
                if niet_lat:
                    twee = niet_lat
                if not twee:
                    flags.append(f"CAP_OVERSCHRIJDING_{dag_naam}")
                    break
                kies = min(twee, key=trim_prio)
                items.remove(kies)
                flags.append(f"OEFENING_GESCHRAPT_CAP_{dag_naam}_{kies['oefening'].get('naam')}")
            totaal = sum(kost(it) for it in items)

        geordend = orden_sessie(items, voorkeur, cyclus, dag_type, flags)
        # BESLUIT 12 juni (Bas): supersets standaard UIT — alleen later in het
        # traject of bij echte tijdnood, via de coach-knop 'supersets_toestaan'.
        # Onderbouwing: cap-model garandeert al dat het schema in de tijd past;
        # supersets kosten 2 stations tegelijk (druk Basic Fit) en vertroebelen
        # RIR-kalibratie bij beginners. Tijdwinst alleen waardevol als tijd echt
        # de bindende beperking is.
        if intake.get("supersets_toestaan"):
            geordend = koppel_arm_supersets(geordend)
        regels = []
        for it in geordend:
            o = it["oefening"]
            reps, rust = schrijf_voor(o, kracht)
            regels.append({"oefening": o.get("naam"),
                           "spier": normaliseer_spier(o.get("naam"), o.get("primaire_spier")),
                           "sets": it["sets"], "reps": reps, "rust": rust,
                           "prehab": it["prehab"], "superset": it.get("superset")})
        sessies.append({"dag": dag_naam, "oefeningen": regels})

    fasen = WEEK_FASEN[kracht]
    # volume_per_spier uit het WERKELIJKE schema (fix 15 juni): tel de daadwerkelijk
    # geplaatste sets per spier in basisweek, i.p.v. het pre-plaatsings-plan (per_dag).
    # Zo klopt de samenvatting altijd met wat de klant in zijn schema ziet — inclusief
    # prehab-sets en afronding bij oefening-splitsing.
    _geplaatst_volume = {}
    for _s in sessies:
        for _o in _s["oefeningen"]:
            _sp = _o.get("spier")
            _geplaatst_volume[_sp] = _geplaatst_volume.get(_sp, 0) + _o.get("sets", 0)

    # TAAK F-vervolg (15 juni) — Optie A: leesbare coach-instructies wanneer een PRIMAIRE
    # spier wel getarget was maar niet (veilig) geprogrammeerd kon worden. Vooral relevant
    # bij blessures die ALLE oefeningen van een spier uitsluiten (bv. knie -> alle quads,
    # elleboog -> alle biceps). De engine forceert NOOIT een gecontra-indiceerde oefening;
    # in plaats daarvan een duidelijke, leesbare instructie zodat de coach die spier zelf
    # handmatig invult met een revalidatie-aanpak die bij de specifieke blessure past.
    PRIMAIR_NAMEN = {"Borst", "Rug", "Schouders", "Biceps", "Triceps", "Quads", "Hams", "Billen"}
    _getarget = {sp for dag in per_dag for sp, n in dag.items() if n > 0}
    _actieve_blessure = actieve_blessure_contra(intake)
    coach_instructies = []
    for _sp in sorted(PRIMAIR_NAMEN & _getarget):
        if _geplaatst_volume.get(_sp, 0) > 0:
            continue  # wel geprogrammeerd — geen instructie nodig
        _pool_met = harde_filters(bib, _sp, intake, eff_ervaring, cyclus)
        if _pool_met:
            coach_instructies.append(
                f"{_sp}: ingepland maar niet geplaatst (capaciteit/plaatsing). "
                f"Controleer het schema of de sessietijd voor deze klant.")
            continue
        _pool_zonder = harde_filters(
            bib, _sp, {**intake, "blessures": [], "pijnlijke_oefeningen": [], "dislikes": []},
            eff_ervaring, cyclus)
        _betrokken = set()
        for _o in bib:
            if _lc(_o.get("primaire_spier")) == _lc(_sp):
                _betrokken |= (_tags(_o.get("contra_indicaties")) & _actieve_blessure)
        if _pool_zonder and _betrokken:
            _bl = "/".join(sorted(_betrokken))
            coach_instructies.append(
                f"{_sp}: NIET automatisch geprogrammeerd — alle {_sp.lower()}-oefeningen zijn "
                f"uitgesloten door de blessure ({_bl}). Vul {_sp.lower()} handmatig in met een "
                f"revalidatie-aanpak die bij deze specifieke blessure past; de engine forceert "
                f"bewust geen gecontra-indiceerde oefening.")
        else:
            coach_instructies.append(
                f"{_sp}: geen passende oefening gevonden (combinatie van blessures, dislikes, "
                f"materiaal of techniekniveau). Controleer de intake of vul handmatig in.")

    return {
        "engine_versie": ENGINE_VERSIE,
        "klant": naam, "cyclus": cyclus,
        "classificatie": {"kracht": kracht, "ervaring": ervaring,
                          "effectieve_ervaring": eff_ervaring, "re_entry": re_entry},
        "capaciteit": {"sessie_cap": cap, "weekbudget": weekbudget},
        "cyclus_focus": {"focus": focus, "spier": focus_accessoire,
                         "reden": rationale},
        "volume_per_spier": {sp: v for sp, v in sorted(_geplaatst_volume.items())
                             if v > 0},
        "weekfasen": [{"week": i + 1, "fase": f, "volume_x": m, "intensiteit": r}
                      for i, (f, m, r) in enumerate(fasen)],
        "basisweek": sessies,
        "flags": sorted(set(flags)),
        "coach_instructies": coach_instructies,
        "notitie": ("Basisweek = 1.0x; de log past de week-multipliers toe. "
                    "Besluiten 11 juni verwerkt: week-plafond (BEG 40+6/dag, FIT n=2 ter bevestiging), TE-floors + direct-min 2, lean 2.0, re-entry BEG 1.0/INT-ADV 0.75. Open: vrouw-cap-bonus."),
    }


def main():
    p = argparse.ArgumentParser(description="BVG selectie-engine v1.2 (volledig getest)")
    p.add_argument("--bibliotheek", required=True)
    p.add_argument("--intake", required=True)
    p.add_argument("--cyclus", type=int, default=1)
    args = p.parse_args()
    with open(args.bibliotheek, "r", encoding="utf-8") as f:
        bib = json.load(f)
    if isinstance(bib, dict):
        bib = bib.get("oefeningen", list(bib.values())[0])
    with open(args.intake, "r", encoding="utf-8") as f:
        intake = json.load(f)
    resultaat = genereer(bib, intake, args.cyclus)
    taxo_fouten = valideer_taxonomie(resultaat)
    if taxo_fouten:
        sys.stderr.write("TAXONOMIE-FOUTEN (output geblokkeerd):\n")
        for f_ in taxo_fouten:
            sys.stderr.write("  - " + f_ + "\n")
        sys.exit(1)
    json.dump(resultaat, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
