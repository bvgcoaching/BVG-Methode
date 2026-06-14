<!-- ============================================================= -->
<!-- MACHINE-LEESBAAR STATUSBLOK — lees dit eerst bij een nieuwe sessie -->
<!-- ============================================================= -->
<!--
DOCUMENT: De BVG Methode — Complete SOP
VERSIE: v3.5 (concept ter review)
DATUM: 14 juni 2026
VORIGE: v3.4 (12 juni 2026)
ENGINE-DOEL: v1.9.0 (na toepassen taak A+B; v3.5 specificeert wat v1.9.0 moet doen)

BESTAND-IDS (Google Drive):
  SOP (deze, v3.4 die vervangen wordt): 1adb32Ae6gu0rM9BiMA443W3AT_UmMSMt
  Engine v1.8.7:                        1UztpfJEjVbek34dWnF19rY1i4EaBefLA
  Bibliotheek v1.7:                     1kuWQ1FS5UicDi3pikR5u3MH9pMlT2qq6
  Intakeformulier:                      1HsTF8itN6jZtTKbqux3vhGVAx8vqGjNJ

WAT v3.5 VERANDERT T.O.V. v3.4 (vier besluiten Bas, 14 juni):
  [B] Vrouw-cap-bonus: placeholder +1 -> VASTGESTELD +2. (§3·CAP)
  [A] Vrouw-billen: blijft hoofdspier, MAAR landmarks GELIJK aan een normale
      primaire spier (NIET hoger dan man). v3.4 zei "hoger dan mannelijke
      accessoire" -> dat was een DENKFOUT (verzonnen capaciteitsbonus; bilspier
      is anatomisch identiek tussen seksen, MRI-genormaliseerd geen verschil).
      Gecorrigeerd. (§5·BILLEN, §11)
  [A] Bil-voorkeur: NIET "dominant ~14-16 sets" (v3.4), MAAR proportionele
      HERVERDELING binnen de been-/FB-dag met MEV-vloer voor quads/hams/kuiten.
      Totaal beenvolume blijft gelijk -> geen extra cap-druk. (§5·BILLEN)
  [A/D] Hip Adduction Machine staat in v1.7 als primaire_spier=Billen, maar is
      binnenbeen (adductoren), GEEN bil. Taggingfout. Uitgesloten uit bil-
      spreiding. Her-taggen hoort in taak D. (§7, §15)

ENGINE-IMPLEMENTATIESTATUS:
  IN ENGINE v1.8.7 (gevalideerd, 40/41 profielen schoon):
    volgorde-laag §8V, breedte-distributie §3, opvulling §4, PPLUL §2,
    vaste accessoire-rotatie §6, hamstring-regel §8V·5.
  GESPECIFICEERD MAAR NOG NIET IN ENGINE (= openstaande code-taken):
    - Taak A: vrouw-billen primair + voorkeur-herverdeling (§5, §11).
      Wijzigingsbestand bestaat: TAAK_A_vrouw_billen_primair.md
    - Taak B: vrouw-cap +2 (§3). Wijzigingsbestand: TAAK_B_vrouw_cap_bonus.md
    - Taak C: herstel-plafond kalibreren (§3) + spillover-verrekening in
      bil-telling. VEREIST draaiende engine + validatie op Owen/Romme. NIET af.
    - Taak D: ladder-tier-review (§7) + Hip Adduction her-taggen. Vakinhoudelijk,
      door Bas. NIET af.

VOLGORDE VAN AFRONDEN: A -> B -> C -> D, DAN pas trainings-log koppelen.
NOG-OPEN-GETALLEN (niet definitief, kalibreren in taak C):
  - vrouw-bil-landmarks (4,8,12,16,20): STARTwaarden, valideren op data.
  - herstel-plafond per krachtniveau: interim 24/30/999 -> herijken (BEG te laag;
    Owen beginner 3d/90min haalt werkelijk ~61 sets/wk). Richting BEG 40-45,
    INT 45-55, ADV ~999. TE VERIFIEREN door engine te draaien.

PERSISTENTIE: na elke wijziging versie ophogen + terug naar Drive/GitHub +
oude versie opruimen. GitHub-repo opzetten (Bas, op laptop) lost het
bestandsoverdracht-probleem structureel op.
-->
<!-- ============================================================= -->

# DE BVG METHODE — COMPLETE SOP (v3.5)
## Capaciteit-eerst trainingsmethodologie

**Status:** concept ter review. v3.5 verwerkt **vier besluiten van 14 juni** en lost twee inconsistenties op die in v3.4 waren geslopen rond de vrouw-billen-regel. De methodiek zelf (de drie ontkoppelde assen, de blokvolgorde, de breedte-distributie) staat — dit is een correctie- en aanscherpingsronde, geen herontwerp.

**Wijzigingen t.o.v. v3.4:**
- **§3·CAP — Vrouw-cap-bonus vastgesteld op +2** (was placeholder +1). Onderbouwd: vrouwen herstellen sneller *tussen sets* (Nuckols/PeerJ 2026, bench press), dus meer werkvolume past in dezelfde sessietijd. Sessie-cap, geen weektotaal-bonus.
- **§5·BILLEN / §11 — Vrouw-billen-regel gecorrigeerd.** Billen blijft een **hoofdspier** voor vrouwen, maar krijgt **gelijke landmarks aan een normale primaire spier** — NIET hoger dan een man. v3.4 stelde hogere landmarks voor ("hoger dan de mannelijke accessoire"); dat was een denkfout. De bilspier is anatomisch identiek tussen seksen en op lichaamsgewicht genormaliseerd is er geen volumecapaciteitsverschil (MRI: genormaliseerd bilspiervolume toont geen sekseverschil — recreatieve-wielrenners-studie, Scientific Reports/PMC10450064). Het sekseverschil in volumecapaciteit zit AL in de sessie-cap (§3, +2) en hoeft niet dubbel geteld in de bil-landmarks.
- **§5·BILLEN — Bil-voorkeur is HERVERDELING, geen volume-explosie.** v3.4 zei dat billen bij voorkeur "dominant ~14-16+ sets" wordt. v3.5: bil-voorkeur **herverdeelt het beschikbare beenvolume proportioneel binnen de dag** (meer bil, evenredig minder quad/ham/kuit) met een **MEV-vloer** zodat geen beengroep onbruikbaar laag zakt. Totaal beenvolume blijft gelijk — consistent met het voorkeurspier-principe (allocatie, geen verzonnen extra capaciteit). De zwaardere variant (echt +volume voor één spier) is en blijft de **Focus-cyclus** (§6), niet de standaard-voorkeur.
- **§7 / §15 — Hip Adduction Machine geflagd als taggingfout.** Staat in v1.7 als `primaire_spier: Billen`, maar adductie is binnenbeen (adductoren), geen bilspier. Uitgesloten uit de bil-spreiding; her-taggen hoort in de ladder-review (taak D).

> **LET OP — implementatiestatus engine:**
> - In engine v1.8.7 geïmplementeerd en gevalideerd (40/41 testprofielen schoon): volgorde-laag (§8·V), breedte-distributie (§3), opvulling (§4), PPLUL (§2), vaste accessoire-rotatie (§6), hamstring-regel (§8·V·5).
> - **Nog NIET in de engine** (= de openstaande code-taken A, B, C): de vrouw-billen-regel (§5/§11), de vrouw-cap-bonus +2 (§3), en het gekalibreerde herstel-plafond (§3). Wijzigingsbestanden voor A en B bestaan en zijn klaar om toe te passen. Tot dat is gebeurd vereist een vrouwelijke bil-voorkeur-klant handmatige bijsturing.

> **Drie punten die op Bas-review/-input wachten:**
> 1. **Ladder-tier-waarden** (bibliotheek v1.7): door Claude ingevuld, formele review open. Inclusief de Hip Adduction-hertagging.
> 2. **Herstel-plafond per krachtniveau** (§3): engine gebruikt interim 24/30/999; BEG is aantoonbaar te laag. Kalibreren door de engine te draaien op Owen/Romme (taak C).
> 3. **Vrouw-bil-landmarks** (§5): startwaarden (4,8,12,16,20) valideren op werkelijke engine-output (taak C).

---

## 0 · KERNPRINCIPE — drie ontkoppelde assen

- **Capaciteit (beschikbare tijd) → VOLUME.** Hoeveel sets iemand doet, volgt uit zijn tijd (geplafonneerd door herstel — §3).
- **Krachtniveau → KWALITEIT.** Cyclus-lengte, RIR vs rep-targets en floors volgen uit hoe sterk iemand is.
- **Ervaring/techniek → OEFENING-MOEILIJKHEID.** Welke oefeningen iemand veilig kan, volgt uit gym-ervaring (+ ladder-instap-gate, §7).

Pijplijn: **tijd in → budget → verdeling → kwaliteit → oefeningen → volgorde → voorschrift.**

De drie assen zijn **onafhankelijk**. Een sterke beginner (hoog krachtniveau, lage ervaring) bestaat; een zwakke gevorderde ook. De engine combineert ze niet tot één getal (geen MIN), maar laat elk z'n eigen ding sturen.

---

## 1 · B1 — INTAKE → CLASSIFICATIE (ontkoppeld)

Levert TWEE losse uitkomsten (geen MIN):

**Krachtniveau (BEG/INT/ADV)** — mediaan over de SBD-lifts (geschatte 1RM ÷ lichaamsgewicht) t.o.v. de krachtdrempels. Stuurt: volume, RIR-schema, cyclus-lengte, progressie-trigger.

**Ervaringsniveau (Novice/Gevorderd/Expert)** — uit de ervaring-dropdown: <1jr→Novice, 1–3jr→Gevorderd, 3–5jr→Gevorderd, 5+jr→Expert. Stuurt: techniek_niveau-filter + novice_only-gating + ladder-instap-gate (§7).

Regels: techniek-gating (W1–2 kan ervaring verlagen); <2 lifts → kracht cap BEG (flag `INSUFFICIENT_STRENGTH_DATA`); 4/4 ADV-ratio's → ADV; 5+jr zonder progressie-tracking → ervaring cap Gevorderd. **Kracht ≠ ervaring is normaal**, geen conflict (flag `KRACHT_ERVARING_MISMATCH_INFO`).

### 1·1RM — 1RM-schatting (vóór ratio-bepaling)
Ingevulde lifts zijn werkgewichten (kg × reps), GEEN 1RM. Schat eerst:
- **Epley (reps ≤ 8):** 1RM = kg × (1 + reps/30). HIGH confidence.
- **Epley+Brzycki gemiddeld (reps 9–12):** MEDIUM.
- **Reps > 12:** Epley + flag `HIGH_REPS_UNRELIABLE_1RM`. LOW.

### 1·DREMPELS — Strength-drempels per sekse

**Mannen (geschatte 1RM ÷ BW):**

| Compound | BEG → INT | INT → ADV |
|:-:|:-:|:-:|
| Bench | ≥ 1,0 | ≥ 1,5 |
| Squat | ≥ 1,5 | ≥ 2,0 |
| Deadlift | ≥ 2,0 | ≥ 2,5 |
| Row (optioneel) | ≥ 0,75 | ≥ 1,1 |

**Vrouwen (geschatte 1RM ÷ BW):**

| Compound | BEG → INT | INT → ADV |
|:-:|:-:|:-:|
| Bench | ≥ 0,6 | ≥ 0,9 |
| Squat | ≥ 1,2 | ≥ 1,6 |
| Deadlift | ≥ 1,6 | ≥ 2,0 |
| Row | optioneel | optioneel |

Aggregatie: mediaan over SBD (row = bonussignaal). ≥50% ADV → ADV; ≥50% INT+ → INT; anders BEG. Sex = "Anders": mannelijke drempels + flag. Age ≥ 50: flag.

### 1·RE — Re-entry / revalidatie-overlay
Tijdelijke overlay op de classificatie **voor cyclus 1**. Triggers: blessure in revalidatie/post-op (<12 mnd) · rode-vlag-profiel · lange onderbreking/detraining.
Past aan (cyclus 1): (1) oefening-pool gecapt op Novice (of één tier onder echt niveau); (2) belasting revaliderend gewricht vermijden; (3) **volume**: bij BEG **vol volume behouden** (factor 1,0 — de voorzichtigheid zit in oefening-keuze, niet in volume), bij INT/ADV volume × 0,80; (4) intensiteit conservatiever.
Exit (na cyclus 1): pijnvrij door volledige ROM + techniek-check + progressie → echte classificatie. Flag `RE_ENTRY_ACTIEF`.

---

## 2 · B2 — SPLIT & FREQUENTIE

| Dagen | Split | Structuur | Freq |
|:-:|:-:|:-:|:-:|
| 2 | FB2 | Full Body A / B | 2× |
| 3 | ULF | Upper / Lower / Full Body | 2× |
| 4 | UL2 | Upper 1 / Lower 1 / Upper 2 / Lower 2 | 2× |
| 5 | **PPLUL** | Push / Pull / Legs / Upper / Lower | bovenlijf 3× · benen 2× |
| 6+ | MANUAL | flag `MANUAL_SPLIT_6PLUS` voor coach-review | — |

Minimaal 2× per spier per week. Voorkeurspier krijgt de frisste dag; Lower niet 2 dagen achter elkaar.

### 2·PPLUL — dagtype-indeling (5-daags)
- **PUSH:** Borst, Schouders, Triceps (+ Core)
- **PULL:** Rug, Biceps (+ Core)
- **LEGS:** Quads, Hams, Billen, Kuiten, Onderrug (+ Core)
- **UPPER:** Borst, Rug, Schouders, Biceps, Triceps (+ Core)
- **LOWER:** Quads, Hams, Billen, Kuiten, Onderrug (+ Core)

Frequentie: borst/schouders/triceps = Push + Upper (2×); rug/biceps = Pull + Upper (2×); benen = Legs + Lower (2×). Bovenlijf wordt 3 van de 5 dagen geraakt (Push, Pull, Upper) — dat is de reden om PPLUL te kiezen. De gespecialiseerde dagen (Push, Pull) dragen het meeste volume per spier (zie §3 breedte-weging); Upper/Lower zijn de aanvullende touch.

### 2·6PLUS — 6+ dagen
De engine levert geen 6+ schema automatisch. Flag `MANUAL_SPLIT_6PLUS`: de coach bouwt handmatig (bv. PPL×2 of een Arnold-split). Bewuste scope-grens — geen klant heeft dit nodig en het risico op fouten is hoog.

---

## 3 · C1 — CAPACITEIT: SESSIE-CAP + DAG-VERDELING

### 3·CAP — Sessie-cap (rust-gedreven)

| Sessieduur | Basis-cap |
|:-:|:-:|
| 45 min | 15 |
| 60 min | 21 |
| 75 min | 27 |
| 90 min | 32 |

- Big-three-straf: elke squat / deadlift / bench-press −3 sets.
- **Vrouw-cap-bonus: +2** (VASTGESTELD 14 juni, was placeholder +1). Caps voor vrouwen: 45→17, 60→23, 75→29, 90→34.
- Weekbudget = dagen × cap (tijd-plafond; landmarks bepalen het werkelijke volume).

**Onderbouwing vrouw-cap-bonus +2.** Vrouwen herstellen sneller *tussen sets* dan mannen (Nuckols et al., PeerJ 2026 — bench press, 75% 1RM, ~90s rust; vrouwen vermoeien langzamer over meerdere sets doordat ze tussen sets meer herstellen, niet doordat ze per set trager vermoeien). Daardoor past binnen dezelfde sessietijd meer werkvolume. Dit is bewust een **sessie-cap-bonus, geen weektotaal-bonus**: het herstel *tussen sessies* is volgens diezelfde data gelijk tussen de seksen, dus de deload-logica blijft ongewijzigd (§11). Effectgrootte op spiergroei is volgens de systematische review (Nuckols, PROSPERO CRD42018094276) vergelijkbaar tussen seksen — het verschil zit in werkcapaciteit per sessie, niet in groei-respons. Het getal +2 is een conservatieve vertaling (~+6–7% bij cap 27–34), bewust niet hoger. **Eerlijke kanttekening:** het bewijs rust overwegend op bench-press-data; voor overige spiergroepen geldt +2 als onderbouwde werkhypothese, niet als bewezen feit.

### 3·HERSTEL — Herstel-plafond
Werkelijk volume = **MIN(tijd-cap, herstel-plafond voor krachtniveau).** Bij BEG ligt het herstel-plafond vaak ónder wat de tijd toelaat.

> ⚠ **INTERIM — kalibreren in taak C.** Engine gebruikt nu 24/30/999 (BEG/INT/ADV) als weektotaal over álle spieren. Dit plafond is een vangnet tegen extremen, geen normaal-geval-rem. De BEG-waarde 24 is aantoonbaar te laag: Owen (beginner, 3 dagen, 90 min) haalt in de praktijk ~61 sets/week zonder herstelproblemen. Voorlopige richting, TE VERIFIEREN door de engine te draaien: BEG 40–45, INT 45–55, ADV ongeplafonneerd (999). Definitief vaststellen pas na meten op Owen/Romme.

### 3·VERDELING — Breedte-gewogen dag-verdeling (v3.4, besluit Bas 12 juni)

**KERNPRINCIPE:** het aandeel van een spier op een dag is **omgekeerd evenredig met hoeveel spiergroepen die dag bestrijkt** (Core telt niet mee — die staat op elke dag). Een brede Full Body-dag (≈8 primaire spieren) krijgt per spier dus minder dan een gerichte Upper/Lower-dag (≈5) of een Push/Pull-dag (2–3).

**Gevolg (option 2, gekozen door Bas):**
- In **U/L/FB** wordt de Full Body-dag automatisch de **lichtere derde touch**; Upper en Lower dragen het hoofdvolume en daarmee de klant-prioriteit. (Owen: 23/22/25 i.p.v. de oude 14/23/28.)
- Bij **symmetrische** splits (FB-A/FB-B, of Upper1/Upper2) zijn de dag-gewichten gelijk → ±50/50.
- In **PPLUL** dragen de gespecialiseerde dagen (Push, Pull) het meeste volume per spier; Upper/Lower vullen aan.

**Regels:**
- **Min-2-vloer:** elke geplaatste spier krijgt ≥2 sets per dag — **nooit 1-set splinters** (besluit Bas). Past 2 sets niet binnen de cap, dan valt de spier terug op één dag.
- **Beschermde spieren eerst:** Core en armen (hard doel) worden vóór de rest geplaatst, zodat tijdgebrek nooit stiekem bij hen terechtkomt.
- **2× frequentie** waar er ≥2 geschikte dagen zijn en elke dag ≥2 sets kan krijgen; anders 1×.

---

## 4 · C2 — VOLUMEVERDELING + OPVULLING

### 4·LAGEN — Twee-lagen-model

**Laag 1 — primaire spieren** (borst, rug, schouders, bi, tri, quads, hams, billen¹): gelijk-totaal-effectief volume (directe + 0,5×indirecte).
- Spillover (effectieve indirecte sets/wk): Borst 0, Rug 0, Schouders 3, Biceps 5,5, Triceps 5,5, Quads 1, Hams 1,5, Billen 3.
- Floors (directe sets): 6 voor {Borst, Rug, Quads, Hams}; 4 voor {Schouders, Biceps, Triceps}. **Armen-floor 4** (BVG-praktijk: 4 directe armsets + compound-spillover, niet RP-MEV 6) — bewust besluit.

> ¹ **Billen-uitzondering, sekse-afhankelijk (zie §5):** voor MANNEN is billen een **accessoire** (laag-2, MEV 0, leunt op squat/hinge/lunge-spillover). Voor VROUWEN is billen een **hoofdspier** (laag-1) met **dezelfde landmark-systematiek als elke andere primaire spier** — niet hoger.

**Laag 2 — accessoires** (vaste onderhoudsdosis, NIET gelijk-TE): Kuiten 4, Core 3, Onderrug 3, + roterende prehab 2. Plus **billen voor mannen** (MEV 0, focus-rotatie kan bumpen).
- Core heeft een **hard weekminimum van 2** (nooit 0).

### 4·OPVUL — Opvul-mechanisme (v3.4, besluit Bas)

Lichte dagen worden aangevuld met accessoires tot **~85% van de sessie-cap**, zodat trainingstijd niet wordt verspild. Regels:
- Vul tot het niveau van de zwaarste 'echte' dag, begrensd op ~85% cap.
- **Nooit een dag oppompen die al zwaar is** (≥80% van het doel) en nooit boven de cap.
- Fill-pools per dagtype: **benen-dagen** → abductie (Billen), Kuiten, Onderrug; **bovenlijf-dagen** → rear-delt/houding (Schouders), Core; **Full Body** → Billen, Core.
- Weekplafonds op fill-volume: Billen 8, Kuiten 6, Onderrug 4, Schouders 4, Core 6.
- **Neveneffect (gewenst):** op benen-dagen geeft dit mannen direct bilwerk (abductie) bovenop de spillover — lost het "billen 0" probleem op zonder de accessoire-status aan te tasten.

Primair-budget = weekbudget − accessoires − prehab.

---

## 5 · B3 — VOORKEURSPIER + BILLEN-SEKSEREGEL

### 5·VOORKEUR — Voorkeurspier
Herverdeling binnen het vaste budget (**geen extra volume** — budget is gecapt). Opener-positie in de sessie (§8·V) + stretch-selectie. In een gecapt budget is de voorkeur bescheiden (+1 totaal-effectieve set bovenop herverdeling) — communiceer dit naar de klant. Flag `TE_VEEL_PRIORITEITEN` bij te veel prioriteiten. De zwaardere variant (echt +volume voor één spier, +50% een mesocyclus lang) is de **Focus-cyclus** (§6), een bewuste opt-in — niet de standaard-voorkeur.

### 5·BILLEN — Billen-sekseregel (GECORRIGEERD v3.5, besluit Bas 14 juni)

> **Wat er t.o.v. v3.4 veranderde, en waarom.** v3.4 gaf vrouw-billen *hogere* landmarks dan een man en liet bil-voorkeur uitgroeien tot een *dominante* spier van ~14–16 sets. Beide zijn in v3.5 gecorrigeerd. Reden: de bilspier is anatomisch identiek tussen seksen en op lichaamsgewicht genormaliseerd is er geen verschil in volumecapaciteit (MRI-data). Een hóger bil-landmark voor vrouwen zou dus een verzonnen capaciteitsbonus zijn. Het reële sekseverschil in volumecapaciteit zit AL in de sessie-cap (§3, +2) en mag niet dubbel geteld worden. En een voorkeurspier hoort volgens het BVG-principe te *herverdelen* binnen een gecapt budget, niet ongelimiteerd te groeien.

**MANNEN — billen = accessoire (laag-2):**
- MEV 0; leunt op squat/hinge/lunge-spillover (effectief ~3 indirecte sets).
- Direct bilwerk alleen via: (a) de accessoire-focus-rotatie wanneer billen aan de beurt is, of (b) het opvul-mechanisme op 4/5-daagse benen-dagen (abductie).
- Rationale: voor een mannelijk fysiek doel zijn glutes goed bediend door zware squat/hinge; direct glute-isolatievolume heeft lage prioriteit.

**VROUWEN — billen = hoofdspier (laag-1):**
- Billen verschuift uit de accessoire-rotatie naar de **primaire spieren**, met **dezelfde landmark-systematiek als elke andere primaire spier** — *niet* hoger dan een man. Startwaarden (MV, MEV, MAV_laag, MAV_hoog, MRV) = **(4, 8, 12, 16, 20)**, geschaald op krachtniveau via de bestaande LANDMARK_INDEX. Deze getallen spiegelen een gemiddelde primaire spier (orde van grootte vergelijkbaar met quads/rug); ze zijn **startwaarden** en worden in taak C gevalideerd op werkelijke engine-output.
- **Default (geen voorkeur):** billen krijgt een **bescheiden primair doel rond MEV (~6–8 directe sets)**, 2×/week. Bewust laag-in-de-band, zodat er bij een latere bil-voorkeur een echte marge is om naartoe te herverdelen (zie volgende punt). Plus squat/hinge-spillover bovenop.
- **Bil-voorkeur:** billen krijgt de **opener-positie + stretch-selectie** (zoals elke voorkeurspier) én een **proportionele herverdeling binnen de been-/FB-dag**:
  - Bil-**doel** bij voorkeur ≈ **MAV_laag (~12 directe sets)** — duidelijk boven het default-anker (~6–8), zodat de voorkeur een merkbaar effect heeft en niet alleen de openerpositie verschuift.
  - Het beschikbare beenvolume schuift richting billen, ten koste van quads/hams/kuiten — **proportioneel**, naar rato van hoeveel elke donor boven zijn MEV-vloer zit.
  - **MEV-vloer:** geen donor (quads/hams/kuiten) zakt onder zijn MEV. Wat niet kan worden verschoven zonder een vloer te doorbreken, wordt niet verschoven.
  - **Als de vloeren het bil-doel blokkeren:** haalt de herverdeling de ~12 niet zonder een donor onder MEV te duwen, dan **stopt het bij wat wél kan** — billen krijgt het maximaal haalbare, de donoren blijven op hun MEV. Flag `BIL_VOORKEUR_GEKNELD_DOOR_MEV_VLOER` zodat zichtbaar is dat tijd/capaciteit de bil-ambitie begrenst (de oplossing is dan meer sessietijd of de Focus-cyclus, niet de vloeren doorbreken).
  - **Totaal beenvolume blijft gelijk** — geen extra cap-druk, herstel blijft in balans. Dit is het wezenlijke verschil met de v3.4-formulering.
  - Variatie over **alle bilpatronen**: hip thrust/bridge (verkort) · 45° hip extension / RDL (gerekt) · abductie (bovenste bil/medius) · lunges/step-ups. Glutes ontvangen daarbovenop nog squat/hinge-spillover.
  - **Reken-eenheid:** de landmarks, de MEV-vloeren en de herverdeling rekenen allemaal in **directe sets**. Spillover (squat/hinge → billen) komt daar in de telling bovenop en wordt pas in **taak C** echt verrekend; tot dan worden billen iets boven hun directe doel bediend (de spillover is "gratis extra"), wat conservatief en veilig is.
- Wil de klant écht een blok lang vol op billen, dan is dat de **Focus-cyclus** (§6, +50% voor één spier, opt-in 1×/jaar) — daar mag het totale bilvolume wél stijgen, ten koste van trim elders. De standaard-voorkeur doet dat niet.
- De bibliotheek v1.7 ondersteunt dit volledig: 11 echte bil-oefeningen over alle patronen (zie §7-noot; de 12e, Hip Adduction Machine, is een taggingfout en telt niet als bil).

> ⚠ **Engine-status:** deze vrouw-billen-regel is nog NIET in engine v1.8.7. Wijzigingsbestand `TAAK_A_vrouw_billen_primair.md` bevat de vier deelwijzigingen (A1 billen primair + vrouw-landmarks; A2 voorkeur-logica + bilpatroon-spreiding; A3 proportionele herverdeling met MEV-vloer; A4 Hip Adduction uitsluiten). De spillover-verrekening (squat/hinge meetellen in de bil-telling) is bewust uitgesteld naar taak C, omdat dat een draaiende engine + validatie vereist. Tot implementatie: handmatige bijsturing van bilvolume voor een vrouwelijke bil-voorkeur-klant.

---

## 6 · CYCLUSSTRUCTUUR + ACCESSOIRE-FOCUS

BEG 8wk, INT 6wk, ADV 5wk. **Deload (vermoeidheid) gescheiden van evaluatie.** Peak verschuift van VOLUME naar INTENSITEIT. Within-week undulatie default-aan voor laag-volume INT/ADV, uit voor beginners. Eerste cyclus volledige calibratie; terugkerende klant ~0,85×.

### 6·FOCUS — Vaste accessoire-focus-rotatie (v3.4, besluit Bas)
Elke cyclus krijgt ÉÉN accessoire (of prehab-thema) de focus: baseline = MEV, focus → richting MAV-laag. De rotatie is **VAST en voorspelbaar** (i.p.v. synergie-weging):

**onderrug → houding → core → kuiten → billen → grip → (herhaalt)**

- Logica: beschermend/fundamenteel eerst (onderrug = fundament onder hinge/squat; houding = schoudergezondheid tegen perswerk; core = rompstabiliteit), aesthetisch/ondersteunend later (kuiten, billen, grip).
- De focus die de **voorkeurspier dupliceert** wordt overgeslagen.
- **Focus-bump schaalt met kracht:** BEG = midden tussen MEV en MAV (geen volle MAV — voorkomt 10 sets core voor een beginner); INT = ~¾ richting MAV; ADV = volle MAV-laag.

> **Onderscheid Focus-rotatie vs Focus-cyclus.** De accessoire-focus-rotatie hierboven is automatisch en bescheiden (één accessoire iets omhoog per cyclus). De **Focus-cyclus** (§5·VOORKEUR, §11) is iets anders: een bewuste klant-opt-in, 1×/jaar, +50% volume voor één gekozen hoofdspier een hele mesocyclus lang. Verwar ze niet.

### 6·BEG — 8 weken (rep-target gestuurd, geen RIR, geen diepe deload)

| Week | Fase | Volume | Sturing |
|:-:|:-:|:-:|:-:|
| 1–2 | Skill/techniek | 0,65× | Beweging leren, licht |
| 3–4 | Belasting opbouwen | 0,80× | Double progression op rep-targets |
| 5–6 | Doorbouwen | 0,90× → 1,0× | Naar volle capaciteit |
| 7 | Piek | 1,0× | Volle capaciteit, techniek leidend |
| 8 | Evaluatie | 0,70× | Hertest sleutellifts + techniek |

### 6·INT — 6 weken (RIR-gestuurd)

| Week | Fase | Volume | Comp. RIR | Iso. RIR |
|:-:|:-:|:-:|:-:|:-:|
| 1 | Calibratie | 0,75× | 3–4 | 2–3 |
| 2 | Opbouw | 0,90× | 2–3 | 1–2 |
| 3 | Piek volume | 1,0× | 2 | 1 |
| 4 | Intensiteitspiek | 1,0× | 1 | 0–1 |
| 5 | Final push | 1,0× | 1 | 0 |
| 6 | Deload | 0,5×/0,7× | 4–5 | 4–5 |

### 6·ADV — 5 weken (RIR-gestuurd, altijd echte deload)

| Week | Fase | Volume | Comp. RIR | Iso. RIR |
|:-:|:-:|:-:|:-:|:-:|
| 1 | Calibratie | 0,80× | 2–3 | 1–2 |
| 2 | Opbouw | 0,95× | 1–2 | 1 |
| 3 | Piek volume | 1,0× | 1 | 0–1 |
| 4 | Intensiteitspiek | 1,0× | 0–1 | 0 |
| 5 | Deload | 0,50× | 4–5 | 4–5 |

**Volume-band stelt bij (INT/ADV):** laag volume (~6–8 TE/spier) → deload wordt lichte 0,7×, RIR ~1 lager op veilige oefeningen (compounds altijd min. RIR 1–2). Hoog volume (~14+) → echte 0,5× deload.

---

## 7 · BIBLIOTHEEK v1.7 + LADDER-SYSTEEM

**Status:** bibliotheek **v1.7** is gemerged (107 oefeningen): v1.4-basis + v1.6-mutaties + ladder-systeem + bil-uitbreiding.
- v1.6-mutaties: 4 verwijderd (walking lunges, 2 DB calf-varianten), Cable Pushdown → Triceps Pushdown, Overhead Cable+DB Extension → Overhead Triceps Extension (attachment-neutraal).
- Bil-uitbreiding (8 → 12): 45 Hip Extension (bil-focus, gerekt), Reverse Lunge (DB), Cable Box Step-up, Hip Adduction Machine.

> ⚠ **Taggingfout (te corrigeren in taak D):** **Hip Adduction Machine** staat met `primaire_spier: Billen`, maar adductie (been naar binnen) traint de **adductoren / binnenbeen**, niet de bil. De echte bil-oefeningen zijn er dus **11**, niet 12. "Hip ABDuction Machine" (been naar buiten → gluteus medius/minimus) is wél correct als Billen getagd. Aanbeveling: her-tag Hip Adduction naar een aparte spiergroep (Adductoren/Binnenbeen) of herclassificeer. Tot dan is de oefening code-matig uitgesloten uit de bil-spreiding (§5).

18-veld schema: naam, primaire_spier, secundaire_spieren, patroon, type, materiaal, stabiliteit, **techniek_niveau**, unilateraal, vermoeidheidskost, belasting_profiel, weerstandsprofiel, contra_indicaties, substitutiegroep, **coach_prioriteit**, **novice_only**, **ladder_familie**, **ladder_position**.

### 7·BIL — Bil-oefeningen in v1.7 (per patroon, voor de spreiding bij vrouw-voorkeur)
- **Bridge:** Barbell Hip Thrust (ladder 2), Machine Hip Thrust (ladder 1), Single-Leg Hip Thrust (ladder 3)
- **Hinge:** Sumo Deadlift (ladder 3)
- **Heupextensie:** 45 Hip Extension bil-focus (ladder 1, gerekt — sterke stretch-opener), Cable Glute Kickback (iso)
- **Lunge:** Step-up (ladder 1), Reverse Lunge DB (ladder 2), Bulgarian Split Squat bil (ladder 3), Cable Box Step-up (ladder 1)
- **Abductie:** Hip Abduction Machine (iso — gluteus medius/minimus)
- ~~Adductie: Hip Adduction Machine~~ → taggingfout, GEEN bil (zie boven)

Spreiding-prioriteit bij bil-voorkeur: Bridge → Hinge → Heupextensie → Lunge → Abductie.

### 7·L — Ladder-systeem
- **ladder_familie:** cluster compounds met gedeeld rotatie-/progressiepad (kan substitutiegroepen overstijgen).
- **ladder_position (tier 1–5):** 1 = makkelijkste instap (machine/ondersteund), hoger = zwaarder/technischer. Canoniek: Leg Press 1 → Hack Squat 2 → Back Squat 3 → Bulgarian Split Squat 4.
- **Geen ladder** (null) voor isolaties, isometrisch werk, core.
- **Singleton-regel:** een compound alleen in zijn familie (Sumo DL, GHR, Weighted Dip) houdt tóch een tier als **instap-gate**.
- **Instap-gate per ervaring:** Novice tier 1–2 · Gevorderd t/m 3 · Expert t/m 4–5. Bovenop het techniek_niveau-filter (bewust redundant).
- **Klimpad:** max +1 tier per cyclusovergang, alleen bij schone progressie + techniek-check. Geen progressie → zelfde tier, andere oefening. Tier-4 unilaterale opties geblokkeerd in cyclus 1.
- ⚠ Tier-waarden door Claude ingevuld (12 juni) — review open (taak D).

---

## 8 · B5 — SELECTIE-MOTOR + VOLGORDE

Per sessie, per spier-slot:

**1. Harde filters (intake):** materiaal beschikbaar · techniek_niveau ≤ ervaring · novice_only-gating · ladder-instap-gate · geen contra-indicatie die botst met blessure · niet in dislikes · niet in pijnlijke_oefeningen.
**2. Structuurregels:** rug = verticale + horizontale trek (over de week); benen-dag krijgt **altijd** een squat-patroon + een hinge; delts → lateraal/achter (niet front-pers); **geen dubbele oefening binnen één sessie** (slots vouwen samen als minder distincte oefeningen beschikbaar dan slots).
**3. Rotatie (ladder-gestuurd):** compounds stabiel BINNEN een cyclus, roteren TUSSEN cycli langs het ladder-pad (max +1 tier). Isolaties roteren vrij; dek over cycli verschillende weerstandsprofielen.
**4. Coach-bias (zacht, 2 van 3):** 2 van 3 cycli leunt op coach-voorkeur; elke 3e = variatie.
**5. Selectie + klant-seed:** deterministisch.
**6. Prehab-slot (default aan):** klein roterend slot (lage rug → houding → grip), contra-aware.
**7. Volgorde-laag:** §8·V hieronder.

**Unilateraal:** telt 1 set voor volume, ~1,5× tijdseenheid voor de cap.

### 8·V — VOLGORDE-LAAG: HARDE BLOKVOLGORDE

De sessie is opgebouwd in **vaste blokken**, in deze volgorde:

**BLOK 1 — grote compounds (borst / rug / benen)**
**BLOK 2 — schouders** (ALLE schouderwerk, ook losse delt-isolaties)
**BLOK 3 — armen** (biceps + triceps)
**ACCESSOIRES** — kuiten / onderrug / prehab
**BLOK 4 — core** (altijd laatst)

**V·1 Opener (wie begint).**
- **Mét voorkeurspier:** die opent altijd, geen rotatie. (Voor een vrouw met bil-voorkeur op een benen-dag: een bil-oefening opent, bij voorkeur een stretch-gerichte zoals 45 Hip Extension of Bulgarian Split Squat — zie §5.)
- **Zónder voorkeurspier (bovenlichaam):** opener **roteert per mesocyclus** — cyclus 1 = rug eerst (kantoordoelgroep, zwakste achterketen; pers lijdt minder onder voorafgaand trekwerk), cyclus 2 = borst, daarna afwisselend. Flag `OPENER_ROTATIE_<spier>`.
- **Benen-dag (LOWER/LEGS):** een been-compound opent (tenzij bil-voorkeur de opener claimt).

**V·2 Push-pull interleave binnen elk blok.** Borst↔rug wisselen af in blok 1; biceps↔triceps in blok 3. Antagonist-herstel, geen extra tijdkost.

**V·3 Guardrail squat/hinge (FULL/LOWER/LEGS).** ÁLS er een squat/hinge-compound is, staat die in ronde 1, **uiterlijk slot 3**. De guardrail dwingt **geen** squat af die er niet is — de wekelijkse bilaterale-squat-cap mag een FB-dag legitiem zonder squat-compound laten (ordening, geen verplichting). Reparatie-flag `GUARDRAIL_SLOT3_GEREPAREERD`.

**V·4 Synergist-bescherming — STRUCTUREEL (niet meer reparatie).** Doordat armen een **apart, later blok** zijn, kan een arm-isolatie nooit vóór een compound landen. Een triceps-isolatie vóór een pers-compound, of biceps-isolatie vóór een trek-compound, is **fysiek onmogelijk** in de blokstructuur. Pre-exhaust is geen engine-optie; wil de coach het ooit, dan is dat een handmatige aanpassing.

**V·5 Hamstring-regel (v3.4, afgerond).**
- **Dedicated benen-dag (LOWER/LEGS):** hams krijgt een **hinge + een curl** wanneer het volume het toelaat.
- **Weekvolume hams ≥ 6:** 2× frequentie — dedicated dag = hinge + curl (≥4 sets daar), secundaire dag (FB) = een hinge.
- **Weekvolume hams < 6:** 1× frequentie — **hinge + curl samen op de dedicated dag** (hinge+curl gaat vóór een tweede wekelijkse touch).
- Symmetrisch met quads (compound + isolatie).

**V·6 Vaste uitzonderingen.** Schouder-uitzondering op upper/full; geen biceps op pure leg day; core/abs altijd laatst.

### 8·BVS — Beginner-vriendelijkheid score (techniek-filter)
1 = vaste-pad machine (W1+) · 2 = geleide free weight (W3+) · 3 = vrije DB/stabiele BB (INT, BEG W6+) · 4 = heavy BB compound (INT/ADV) · 5 = skill-intensive/plyometric (ADV).

### 8·RUG — De Rug-regel
Elke Upper/FB/Pull day: min. 1 vertical pull + 1 horizontal pull.

---

## 9 · B6 — VOORSCHRIJVEN: reps / RIR / tempo / rust

**Beginner-RIR-regel:** BEG progresseert op rep-targets, RIR losse richtlijn ("laat 3–4, nooit grinden"), two-session-trigger als vangnet. INT/ADV: precieze RIR per week (§6; compounds altijd 1 RIR hoger dan isolaties).

### 9·REPS — Rep-ranges

| Categorie | BEG | INT | ADV |
|:-:|:-:|:-:|:-:|
| Heavy compound | n.v.t. | 5–8 | 4–6 / 5–8 |
| Standard compound | 8–12 | 6–10 | 5–8 |
| Isolatie stretch | 10–15 | 8–12 | 6–10 |
| Isolatie peak | 10–15 | 10–15 | 8–12 |
| Lateral raise | 12–15 | 12–15 | 10–12 |
| Kuiten gastroc (standing) | 10–15 | 8–12 | 6–10 |
| Kuiten soleus (seated) | 15–20 | 12–20 | 10–15 |
| Core dynamisch | 10–15 | 10–15 | 10–15 |
| Core isometrisch | 30–60s | 45–75s | 60–90s |

**Double progression:** rep-range is absoluut plafond. Start onderaan, +1–2 reps/sessie tot bovenkant op target-RIR → dan +gewicht, reps terug naar onderkant.

### 9·TEMPO — Tempo (E-I-C-P, seconden)
Heavy compounds 2-0-X-0 · Standard 2-0-1-0 · Stretch-isolaties 3-1-1-0 · Peak-isolaties 2-1-1-0 · Lateral raises 2-0-2-0 · Kuiten 2-1-1-1.

### 9·RUST — Rust
Heavy compound (BB squat/DL) 2,5–3 min · Standard compound 2 min · Isolatie grote spier 90–120 s · Isolatie kleine spier 60–90 s · Kuiten 60–90 s · Core 45–60 s.

---

## 10 · B7 — STARTGEWICHTEN & PROGRESSIE

Vier scenario's: directe 1RM → proxy → starter-tabel → calibratie-vangnet (W1–2). (Volledige proxy-coëfficiënten, starter-tabel en increments ongewijzigd t.o.v. v3.3 — zie B7-tabellen daar; deze sectie is inhoudelijk niet gewijzigd in v3.4/v3.5.)

Kerngetallen: W1_factor 0,90 compounds / 0,85 isolaties; safety 0,95. % van 1RM: 5 reps=87% · 8=78% · 10=73% · 12=70% · 15=65%.
Increments: Quads/Hams/Glutes compound +5 / iso +2,5 · Rug/Borst +2,5 / +1,25 · Schouders compound +2,5 / lateral +1 · Biceps/Triceps +1,25 · Kuiten +5 · Core +2,5.
Cross-cyclus: volume gecapt door tijd → progressie = load + rep-emphasis + isolatie-rotatie **+ ladder-klim waar verdiend**.

---

## 11 · VROUW-KALIBRATIE (herzien v3.5)

- Relatieve hypertrofie vergelijkbaar tussen seksen. **Sneller herstel tussen sets → hogere sessie-cap (§3, +2 vastgesteld).** Tussen-sessie-herstel vergelijkbaar → deload-logica ongewijzigd.
- **GEEN menstruele periodisering** (bewijs nul — autoregulatie bij symptomen, flag `MENSTRUELE_SYMPTOMEN_AUTOREG`). Rep-ranges iets hoger.
- **Billen = hoofdspier (§5·BILLEN):** billen staat in laag-1 met **dezelfde landmark-systematiek als elke andere primaire spier** (startwaarden 4,8,12,16,20 — niet hoger dan een man; de bilspier is anatomisch identiek tussen seksen). Bij bil-voorkeur krijgt billen de opener + stretch-selectie + een **proportionele herverdeling binnen de been-/FB-dag** (meer bil, evenredig minder quad/ham/kuit, MEV-vloer, totaal gelijk). Variatie over alle bilpatronen (hip thrust, gerekte hip extension/RDL, abductie, lunges/step-ups), plus squat/hinge-spillover. ⚠ engine-implementatie pending (taak A).
- **Waarom geen extra bil-capaciteitsbonus voor vrouwen?** Het reële sekseverschil in volumecapaciteit ("vrouwen kunnen meer werk per sessie aan") zit al in de sessie-cap (+2). Dat werkt automatisch door naar billen wanneer die primair zijn. Een tweede, bil-specifieke bonus zou dubbeltelling zijn óf een verzonnen getal — beide ondermijnen de wetenschappelijke integriteit van de methode.
- Onderlichaam-nadruk loopt via het voorkeurmechanisme (herverdeling) en de Focus-cyclus voor wie écht een blok lang vol op billen wil — niet via losse hardcoding of opgeblazen landmarks.

---

## 12 · PREHAB / ACCESSOIRE-GEZONDHEID
Roterend slot voor lage rug, mid/lage traps + houding (face pull), grip/voorarm (carry/hammer). **Default aan.** Laag volume, gezondheidsgericht, contra-aware.

---

## 13 · FASE 3 — OPERATIONEEL (het schema laten leven)

### 13·A · Gemiste sessies & weken
Eén gemiste sessie: pak de eerstvolgende geplande sessie als normaal, niet dubbelen. Hele week <1 wk weg → hervat iets lichter; 1–3 wk → één fase terug; >3–4 wk/ziekte → terugkerende-herstart (~0,85×) of re-entry-overlay. Chronisch <80% adherence → frequentie verlagen naar wat haalbaar is (flag `ADHERENCE_LAAG`).

### 13·B · Stagnatie-/plateaudetectie
BEG (rep-gebaseerd): plateau = geen rep-/gewichtsprogressie over 2 sessies. INT/ADV (RIR): RIR daalt structureel zonder load-vooruitgang over ~1–2 wk. Lokaal vs systemisch: één oefening = lokaal; meerdere lifts tegelijk = onderherstel (C).

### 13·C · Onderherstel-autoregulatie
Trapsgewijs: (1) slechte dag → 1 RIR extra + laatste 1–2 iso-sets schrappen; (2) ≥1 wk → deload naar voren / lichte week; (3) structureel → capaciteit-budget omlaag (verlaagt herstel-plafond §3). Flag `ONDERHERSTEL_AUTOREG`.

### 13·D · Undulatie
Binnen de week (INT/ADV, ≥2×/spier): dag 1 zwaarder/lager-rep + meer rust, dag 2 lichter/hoger-rep/metabool. Beginners GEEN undulatie. Deload = lichtere week, geen vrije week.

### 13·E · Meta-regel
Eén slechte sessie → niets veranderen. Twee sessies stagnatie op één oefening → lokaal ingrijpen. Systemische terugval → C. Chronische adherence <80% → frequentie herzien. **Default = doorzetten.**

---

## 14 · FLAGS (operationeel)
`TE_VEEL_PRIORITEITEN`, `MENSTRUELE_SYMPTOMEN_AUTOREG`, `INSUFFICIENT_STRENGTH_DATA`, `HIGH_REPS_UNRELIABLE_1RM`, `RE_ENTRY_ACTIEF`, `ONDERHERSTEL_AUTOREG`, `ADHERENCE_LAAG`, `KRACHT_ERVARING_MISMATCH_INFO`, `TIJDBUDGET_KNELT_ONDER_LANDMARK`, `HERPLAATSING_RONDE_TEKORT_<n>`, `OPENER_ROTATIE_<spier>`, `GUARDRAIL_SLOT3_GEREPAREERD`, `GUARDRAIL_LOWER_ZONDER_SQUAT_HINGE`, `OPVUL_ACCESSOIRES_<...>`, `MANUAL_SPLIT_6PLUS`, `BIL_VOORKEUR_GEKNELD_DOOR_MEV_VLOER`.

---

## 15 · NOG OPEN (volgorde A → B → C → D, dán log)

**Code-taken engine (op volgorde):**
- **Taak A — vrouw-billen-regel implementeren** (§5/§11). Wijzigingsbestand `TAAK_A_vrouw_billen_primair.md` klaar. Vier deelwijzigingen: billen primair + vrouw-landmarks, voorkeur-logica + bilpatroon-spreiding, proportionele herverdeling met MEV-vloer, Hip Adduction uitsluiten.
- **Taak B — vrouw-cap +2** (§3). Wijzigingsbestand `TAAK_B_vrouw_cap_bonus.md` klaar. Eén constante.
- **Taak C — herstel-plafond kalibreren** (§3) + spillover-verrekening in bil-telling. ⚠ VEREIST draaiende engine + validatie op Owen/Romme. Niet af; gevoeligst. BEG-plafond aantoonbaar te laag (Owen ~61 sets/wk werkelijk).
- **Versie ophogen** na A+B: engine 1.8.7 → 1.9.0.

**Vakinhoudelijk (Bas):**
- **Taak D — ladder-tier-review** (v1.7) bevestigen + **Hip Adduction Machine her-taggen** (nu fout als Billen; is binnenbeen).
- **Vrouw-bil-landmarks** (4,8,12,16,20) valideren op werkelijke engine-output (samen met taak C).

**Daarna:**
- **Intakeformulier gelijktrekken** (stap 4): materiaal-checklist i.p.v. gym-type; likes/dislikes op oefening-niveau; re-entry-type (blessure vs detraining) als veld. Bestand-ID `1HsTF8itN6jZtTKbqux3vhGVAx8vqGjNJ`.
- **Trainings-log koppelen** aan engine-output in Supabase (project `fcvdbazeamuefxnnzlwv`). Owen eerst. NOOIT deployen zonder Bas-review.
- **Voeding/herstel-scope:** schema = puur training; lichaamscompositie vereist voeding (apart traject).

**Infrastructuur:**
- **GitHub-repo opzetten** (Bas, op laptop) → lost het bestandsoverdracht-probleem tussen sessies structureel op. Daarna: elke sessie `git clone` → engine draaien → commit terug.

---

## 16 · CHANGELOG / EDITORIAL
- **v3.5 (14 juni 2026):** vier besluiten verwerkt. Vrouw-cap-bonus vastgesteld op +2 (§3). Vrouw-billen-regel **gecorrigeerd**: billen blijft hoofdspier voor vrouwen maar krijgt gelijke landmarks aan een normale primaire spier (NIET hoger dan man — v3.4-formulering was een denkfout; bilspier anatomisch identiek tussen seksen, sekseverschil zit al in de cap). Bil-voorkeur = proportionele **herverdeling** binnen de dag met MEV-vloer, totaal beenvolume gelijk (was: dominant ~14–16 sets). Hip Adduction Machine geflagd als taggingfout (binnenbeen, geen bil) — uitgesloten uit bil-spreiding, her-taggen in taak D. Machine-leesbaar statusblok bovenaan toegevoegd voor sessie-overdracht.
- **v3.4 (12 juni 2026):** gelijkgetrokken met engine v1.8.7. Harde blokvolgorde (§8·V), synergist-als-structuur, hamstring-regel afgerond, PPLUL toegevoegd (§2), breedte-gewogen distributie + opvulling (§3/§4), vaste accessoire-rotatie + krachtgeschaalde focus-bump (§6), vrouw-billen-regel gespecificeerd (§5/§11, engine-implementatie pending).
- **v3.3:** volgorde-laag + ladder-systeem geïntegreerd; bibliotheek v1.7-merge.
- **Bekende doc/engine-divergentie:** de vrouw-billen-regel (§5/§11), vrouw-cap +2 (§3) en gekalibreerd herstel-plafond (§3) staan vóór de engine uit — bewust (specificatie eerst, implementatie via taken A/B/C).
