# ⚡ AI-Sähkövahti Home Assistant Integration (Pro & VIP)

*Finnish guide follows below — Suomenkielinen ohje löytyy alempaa.*

---

## 🌍 Overview (English)

**AI-Sähkövahti** is a Home Assistant integration and automation package built around electricity spot-price markets, weather-aware price forecasting (24h, 7d, 30d), thermal mass pre-heating, and local load/fuse management.

- **Live Dashboard & Free 24h Tier:** https://aisahkovahti.65.109.171.178.sslip.io *(Web UI currently in Finnish; English version coming soon)*
- **Plans & Licensing:** Free 24h testing available via the site; **Pro** (7d) and **VIP** (30d) memberships are available via Gumroad (`https://hawknet.gumroad.com/`). License validation is performed via standard outbound HTTPS API requests.
- **Local-First Security (Pull-Only):** No inbound ports or external access to your Home Assistant instance are required. The custom component only makes outbound HTTPS requests to fetch forecasts and validate license status; all heating decisions, safety limits, and relay actions run locally in Home Assistant.
- **Thermal Mass, Zones & Price Caps (`packages/thermal_mass_learning.yaml`):**
  - Calculates heating demand hours using 24h outdoor temperature anchor points (`-30 °C` to `+15 °C`) blended with optional local outdoor and wind-chill sensors.
  - Separates living-area sensors (e.g. `p1`, `p2`, 1st/2nd floor) from crawlspace/basement buffer zones so crawlspace frost or dry cold air never forces expensive whole-house heating.
  - Supports concrete slab sensor depth (`none`, `deep_35_50mm`, `shallow_or_near_pipe`) or smoothed return water temperature, user-adjustable target temperatures and max indoor drop limits, `cheapest_hours_only` / `max_price_cap` (c/kWh) / `combined_cheapest_and_cap` modes, and an **advisory approve-first** (`advisory_approve`) notification workflow.

### Quick 3-Step Setup for Local Price Sensors or Custom APIs (Outside `FI`)
1. **Select Area & Currency:** Choose your bidding area (such as `SE1`–`SE4`, `NO1`–`NO5`, `DK1`–`DK2`, `EE`, `LV`, `LT`, `GER`/`DE`, `AT`, `NL`, `BE`, `FR`, `PL`, `UK`, `CH`, `CZ`, `SK`, `HU`, `RO`, `ES`, `PT`, `IT`) and currency (`AUTO` or `EUR`, `SEK`, `NOK`, `DKK`, `PLN`, `GBP`, `CHF`, `CZK`, `HUF`, `RON`).
2. **Choose Your Price Source:** Select **Oma Home Assistant -hintasensori** (`ha_entity`) to read directly from your existing local Home Assistant price sensor (such as Nord Pool HACS, ENTSO-E HACS, Tibber, Octopus, or Awattar), or choose **Oma API-osoite** (`custom_api`) and enter your endpoint URL (with optional `{area}` / `{currency}` placeholders) and API key.
3. **Adjust Unit & Multiplier if Needed:** Keep `price_multiplier` at `1.0` when your sensor already uses the target subunit (such as `c/kWh`, `öre/kWh`, `øre/kWh`, `gr/kWh`, or `p/kWh`), or set e.g. `100.0` if your sensor reports prices in major currency units per kWh.

---

## 🔒 Security & Licensing

A free 24-hour trial tier is available through the website, along with **Pro** and **VIP** memberships available on Gumroad: [https://hawknet.gumroad.com/](https://hawknet.gumroad.com/).

- **Server-Verified Licensing:** Enter your personal license key during setup. The integration verifies subscription validity via an outbound HTTPS request and detects your tier (**Pro** or **VIP**) automatically. No open ports or inbound access to your Home Assistant instance are required.
- **Multi-Layered Safety Guardrails:** Includes built-in **Legionella safety monitoring** (min. +55 °C, overridable by the user when needed), main and sub-panel **fuse/power protection**, heat pump **COP low-temperature limits**, heating circuit **fault diagnostics**, home battery **UPS reserve protection**, post-vacation **return disinfection**, and **Advisory Approve-First** (`advisory_approve`) notifications.

---

## 📂 Repository Structure

Both the ZIP package and the GitHub repository follow this layout:

~~~text
aisahkovahti/
├── custom_components/
│   └── aisahkovahti/
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       └── sensor.py
├── blueprints/
│   └── automation/
│       └── aisahkovahti/
│           ├── water_heater_smart_control.yaml
│           ├── ev_smart_charging.yaml
│           ├── battery_optimization.yaml
│           ├── solar_excess_optimization.yaml
│           └── thermal_mass_preheating.yaml
├── device_profiles/
│   ├── cars.yaml
│   ├── heat_pumps.yaml
│   ├── heating_circuits.yaml
│   └── safety.yaml
├── packages/
│   ├── aisahkovahti_profiles.yaml
│   └── thermal_mass_learning.yaml
└── README.md
~~~

---

## 🚀 Home Assistant Installation

### 1. Extract the ZIP Package and Copy Files
Download the ZIP package (or clone this repository) and extract its contents.

Copy these four folders directly into your Home Assistant `/config/` directory:
- `custom_components/aisahkovahti/`
- `blueprints/automation/aisahkovahti/`
- `device_profiles/`
- `packages/`

### 2. Enable `packages` in `configuration.yaml`
To load dynamic vehicle profiles, panel safety power limits, override switches, vacation/maintenance modes, the thermal mass learning package (`thermal_mass_learning.yaml`), and the audit log automatically, make sure your `/config/configuration.yaml` contains the following under `homeassistant:`:

~~~yaml
homeassistant:
  packages: !include_dir_named packages
~~~

*(If you already have a `homeassistant:` section, add only `packages: !include_dir_named packages` indented by two spaces beneath it.)*

### 3. Restart Home Assistant and Add the Integration
1. Restart Home Assistant (**Settings -> System -> Restart**).
2. Go to **Settings -> Devices & Services**.
3. Click **Add Integration** in the bottom-right corner and search for **AI-Sähkövahti**.
4. Enter your valid license key (or free 24h key), select your bidding area and currency, configure a local Home Assistant price sensor or custom API endpoint when outside `FI`, and let the integration detect your tier automatically.

---

## ⚙️ Device Profiles, Packages & Distribution Panels (`device_profiles/` & `packages/`)

You can tailor your property's equipment, control modes, schedules, overrides, and fuse limits by editing the YAML files under `/config/device_profiles/` and `/config/packages/`:

- **`packages/thermal_mass_learning.yaml`**: Calculates 24h heating demand hours from outdoor temperature anchor points (`-30 °C` → `14 h`, `+15 °C` → `0 h`), local weather sensors (outdoor temperature and wind-chill factor), zone sensors (`p1`, `p2`, 1st/2nd floor vs. crawlspace/basement), and slab sensor depth (`none`, `deep_35_50mm`, `shallow_or_near_pipe`). Also includes price-cap modes (`cheapest_hours_only`, `max_price_cap`, `combined_cheapest_and_cap`), user-adjustable living-area drop limits, crawlspace frost/humidity alerts without forcing whole-house heating, and **Advisory Approve-First** (`advisory_approve`) notifications.
- **`packages/aisahkovahti_profiles.yaml`**: Dynamic profiles, panel safety power limits, override switches, vacation/maintenance modes, and audit logging.
- **`cars.yaml`**: EV and PHEV battery capacities (kWh), max currents (A), target state-of-charge (%), buffer reserves (`buffer_kwh`), and per-vehicle charging rules (`charging_rules`: cheap hours, price cap, schedules, and force override).
- **`heat_pumps.yaml`**: Air-to-air and air-to-water heat pump zones, COP low-temperature cutoffs, temperature control modes (`temp_control`: fixed target or `outdoor_temp + offset`), and vacation/maintenance modes (`operating_rules`).
- **`heating_circuits.yaml`**: Underfloor/ceiling heating circuits and electric radiator groups with rated power, fault anomaly monitoring, zone target temperatures (fixed or offset), schedules, and vacation settings.
- **`safety.yaml`**: Main panel (e.g. 3x25A) and any separate sub-panels (such as a garage or yard panel) safety power limits (kW), override and schedule exceptions (`overrides_and_schedules`), and vacation maintenance and return disinfection rules (`vacation_and_hygiene`).

After editing profile files, you can reload them without restarting Home Assistant by calling the `aisahkovahti.reload_profiles` service under Developer Tools.

---

## 🎛️ Control Modes, Overrides & Vacation / Maintenance Mode

All blueprints and helper entities support these user-selectable behaviors:

- **Selectable control mode per device and automation:**
  - *Cheapest hours and price cap*
  - *Schedule only* (e.g. night window `22:00–07:00`)
  - *Combined (schedule + cheapest hours)*
  - *No price or schedule restriction*
- **Advisory Approve-First (`advisory_approve`) or automatic execution:** Request approval via mobile notification before starting heating or charging.
- **Immediate user force override:** Start heating, battery charging, or EV charging right away even during expensive hours or outside schedules (main fuse protection remains active).
- **Overridable safety limits:** Temporarily override water heater minimum temperature or home battery UPS reserve thresholds across expensive price spikes when needed.
- **Zone temperature modes (fixed vs. outdoor temperature + offset):** Set room or floor targets either as fixed values (e.g. `21.0 °C` or `17.0 °C`) or tracking outdoor temperature with an adjustable offset (e.g. `outdoor_temp + 2.0 °C`).
- **Vacation / maintenance mode & return disinfection:** Lower selected zones to a maintenance temperature (e.g. `10 °C`) for a configured duration (e.g. 30 days, up to 180 days) and optionally turn off the water heater during absence. When vacation mode ends, automation can run a disinfection cycle (`+65 °C`) during cheap hours before returning to normal control.

---

## 🤖 Using the Automation Blueprints

Once installed, create automations from the included blueprints under **Settings -> Automations & Scenes -> Blueprints**:

1. **Smart Water Heater Control & Legionella Guard (`water_heater_smart_control.yaml`)**
  - Optimizes water heating around cheap hours, price caps, or schedules, respects panel power limits, and supports an overridable `+55 °C` Legionella guard, force override, vacation shutoff, and return disinfection.
2. **EV Smart Charging (`ev_smart_charging.yaml`)**
  - Starts charging during optimal hours, under a price cap, or on schedule using the active vehicle profile current, supports immediate force override, and monitors the selected main or sub-panel (home or separate garage) fuse limit.
3. **Thermal Mass Pre-Heating & Zone / Maintenance Control (`thermal_mass_preheating.yaml`)**
  - Controls zone temperatures via fixed targets or `outdoor_temp + offset` while respecting min/max/comfort limits, schedules, COP low-temperature cutoffs, price spike warnings, and vacation/maintenance mode.
4. **Solar Excess & Cheap Hours Optimization (`solar_excess_optimization.yaml`)**
  - Routes excess PV production to a water heater, charger, or other loads with hysteresis, alongside optional cheap hours, schedules, force override, and home battery minimum reserve override.
5. **Home Battery & UPS Reserve Smart Control (`battery_optimization.yaml`)**
  - Charges home batteries during cheap hours, under a price cap, or on schedule within fuse limits, supports force charging override, and discharges during price spikes while protecting the UPS reserve level.

---

## 📞 Contact & Support

Have questions, need help with setup, or want to discuss commercial collaboration?

- **Email & Inquiries:** `verkkohaukka@gmail.com`
- **Discord Community:** [https://discord.gg/SnBhsXpAW7](https://discord.gg/SnBhsXpAW7)
- **AI-Sähkövahti:** [https://aisahkovahti.65.109.171.178.sslip.io/](https://aisahkovahti.65.109.171.178.sslip.io/)

*AI-Sähkövahti / VerkkoHaukka® — All rights reserved.*

---
---

# ⚡ AI-Sähkövahti Home Assistant Integration (Pro & VIP)

Tervetuloa AI-Sähkövahdin viralliseen Home Assistant -integraatiopakettiin! Tämä paketti mahdollistaa sähkömarkkinoiden älykkään ohjauksen, hintojen ennakoinnin (Pro 7 vrk / VIP 30 vrk), dynaamiset laiteprofiilit, joustavat aikataulu- ja ohitusvalinnat sekä pää- ja ryhmäkeskuskohtaisen kuormanhallinnan turvallisesti.

---

## 🔒 Turvallisuus ja Lisenssi

Paketin käyttöön on saatavilla ilmainen 24h kokeilutaso sivuston kautta sekä **Pro-** tai **VIP-jäsenyys** (hankittavissa Gumroadista: [https://hawknet.gumroad.com/](https://hawknet.gumroad.com/)).

- **Palvelinvarmennettu lisenssi:** Asennuksen yhteydessä syötetään henkilökohtainen lisenssiavain. Palvelin tarkistaa tilauksen voimassaolon ulospäin suuntautuvalla HTTPS-pyynnöllä ja määrittää tilaustason (**Pro** tai **VIP**) automaattisesti. Avoin portteja tai ulkoista pääsyä käyttäjän Home Assistantiin ei tarvita.
- **Monitasoinen turvakerros:** Paketti sisältää sisäänrakennetun **Legionella-turvavahdin** (min. +55 °C, tarvittaessa käyttäjän ohitettavissa), pää- ja ryhmäkeskuskohtaisen **sulakesuojan**, lämpöpumppujen **COP-pakkasrajan**, lämmityspiirien **vikadiagnostiikan**, kotiakuston **UPS-varavirtasuojan**, loman jälkeisen **paluudesinfioinnin** sekä **Ehdota → Hyväksy** (`advisory_approve`) -ilmoitusmahdollisuuden.

---

## 🌍 Monimaatuki, Valuutat ja Oma Hintalähde (Ruotsi, Norja, Tanska, Baltia, Eurooppa)

AI-Sähkövahti tukee useita Euroopan hinta-alueita (`FI`, `SE1`–`SE4`, `NO1`–`NO5`, `DK1`–`DK2`, `EE`, `LV`, `LT`, `GER`/`DE`, `AT`, `NL`, `BE`, `FR`, `PL`, `UK`, `CH`, `CZ`, `SK`, `HU`, `RO`, `ES`, `PT`, `IT`) ja valuuttoja (`AUTO` tai `EUR`, `SEK`, `NOK`, `DKK`, `PLN`, `GBP`, `CHF`, `CZK`, `HUF`, `RON`).

- **Paikallinen Home Assistant -hintasensori (`ha_entity`):** Erityisesti muissa maissa (kuten Ruotsissa `SE1–SE4`, Norjassa `NO1–NO5`, Tanskassa `DK1–DK2`, Virossa/Latviassa/Liettuassa, Saksassa, Itävallassa, Puolassa tai Britanniassa) käyttäjällä on usein jo valmiina oma hintasensori (esim. Nord Pool HACS, ENTSO-E HACS, Tibber, Octopus tai Awattar). Valitsemalla `ha_entity`-tilan ja oman sensorisi integraatio lukee hinnat suoraan paikallisesti omassa Home Assistantissasi.
- **Oma API-osoite (`custom_api`):** Vaihtoehtoisesti voit syöttää oman hintarajapinnan URL-osoitteen (tukee `{area}`- ja `{currency}`-paikkamerkkejä) sekä valinnaisen API-avaimen.
- **Yksikkökerroin ja valuutta:** `AUTO`-valuutta valitsee maan oletusvaluutan ja alayksikön (esim. `SEK` → `öre/kWh`, `NOK`/`DKK` → `øre/kWh`, `EUR` → `c/kWh`, `PLN` → `gr/kWh`, `GBP` → `p/kWh`), ja `price_multiplier`-kertoimella (esim. `1.0` tai `100.0`) voit mukauttaa hinnan yksikön täsmälleen paikallisen sensorisi mukaan.

---

## 📂 Tiedostorakenne (Repository Structure)

ZIP-paketti ja GitHub-repositorio noudattavat seuraavaa rakennetta:

~~~text
aisahkovahti/
├── custom_components/
│   └── aisahkovahti/
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       └── sensor.py
├── blueprints/
│   └── automation/
│       └── aisahkovahti/
│           ├── water_heater_smart_control.yaml
│           ├── ev_smart_charging.yaml
│           ├── battery_optimization.yaml
│           ├── solar_excess_optimization.yaml
│           └── thermal_mass_preheating.yaml
├── device_profiles/
│   ├── cars.yaml
│   ├── heat_pumps.yaml
│   ├── heating_circuits.yaml
│   └── safety.yaml
├── packages/
│   ├── aisahkovahti_profiles.yaml
│   └── thermal_mass_learning.yaml
└── README.md
~~~

---

## 🚀 Asennusohjeet Home Assistantiin

### 1. Pura ZIP-paketti ja kopioi tiedostot
Lataa ZIP-paketti (tai kloonaa tämä repositorio) ja pura sen sisältö.

Kopioi seuraavat neljä kansiota suoraan Home Assistant -palvelimesi `/config/`-juurikansioon:
- `custom_components/aisahkovahti/`
- `blueprints/automation/aisahkovahti/`
- `device_profiles/`
- `packages/`

### 2. Ota `packages`-kansio käyttöön `configuration.yaml`-tiedostossa
Jotta dynaamiset autoprofiilit, keskusten turvatehorajat, ohituskytkimet, loma-/ylläpitotilat, lämpömassan oppimispaketti (`thermal_mass_learning.yaml`) ja audit-loki latautuvat automaattisesti, varmista että Home Assistantin `/config/configuration.yaml`-tiedostossa on `homeassistant:`-lohkon alla seuraava rivi:

~~~yaml
homeassistant:
  packages: !include_dir_named packages
~~~

*(Jos tiedostossa on jo `homeassistant:`-otsikko, lisää vain rivi `packages: !include_dir_named packages` sen alle kahdella välilyönnillä sisennettynä.)*

### 3. Käynnistä Home Assistant uudelleen ja lisää integraatio
1. Käynnistä Home Assistant uudelleen (**Asetukset -> Järjestelmä -> Käynnistä uudelleen**).
2. Mene kohtaan **Asetukset (Settings) -> Laitteet ja palvelut (Devices & Services)**.
3. Klikkaa oikeasta alakulmasta **Lisää integraatio (Add Integration)** ja etsi listalta **AI-Sähkövahti**.
4. Syötä voimassa oleva lisenssiavaimesi (tai ilmainen 24h-avain), valitse hinta-alue (`FI`, `SE3`, `NO1` jne.) ja valuutta sekä valitse tarvittaessa oma paikallinen Home Assistant -hintasensori tai oma API-osoite. Integraatio tunnistaa tilaustasosi automaattisesti.

---

## ⚙️ Laiteprofiilit, Paketit ja Ryhmäkeskukset (`device_profiles/` & `packages/`)

Voit räätälöidä kiinteistösi laitteet, ohjaustavat, aikataulut, ohitukset ja sulakerajat muokkaamalla `/config/device_profiles/`- ja `/config/packages/`-kansioiden YAML-tiedostoja:

- **`packages/thermal_mass_learning.yaml`**: Laskee 24 h lämmitystuntitarpeen ulkolämpötilan ankkuripisteistä (`-30 °C` → `14 h`, `+15 °C` → `0 h`), paikallisista sääantureista (ulkolämpötila ja tuulikerroin), vyöhykeantureista (`p1`, `p2`, 1./2. kerros vs. ryömintätila/kellari) ja laatta-anturin syvyydestä (`none`, `deep_35_50mm`, `shallow_or_near_pipe`). Sisältää myös hintakattotilat (`cheapest_hours_only`, `max_price_cap`, `combined_cheapest_and_cap`), käyttäjän säätämän asuintilan pudotusrajan, ryömintätilan pakkas-/kosteusilmoitukset ilman talon lämmityspakkoa sekä **Ehdota → Hyväksy** (`advisory_approve`) -ilmoitukset.
- **`packages/aisahkovahti_profiles.yaml`**: Dynaamiset profiilit, keskusten turvatehorajat, ohituskytkimet, loma-/ylläpitotilat ja audit-loki.
- **`cars.yaml`**: Sähköautojen ja lataushybridien akkukapasiteetit (kWh), maksimivirrat (A), tavoitevaraukset (%), varakapasiteetit (`buffer_kwh`) sekä autokohtaiset lataussäännöt (`charging_rules`: halvat tunnit, hintakatto, aikataulut ja pakko-ohitus).
- **`heat_pumps.yaml`**: Ilmalämpöpumppujen (ILP) ja vesi-ilmalämpöpumppujen (VILP) vyöhykkeet, COP-pakkasrajat, lämpötilatavat (`temp_control`: kiinteä tavoite tai `ulkolämpötila + offset`) sekä loma-/ylläpitotilat (`operating_rules`).
- **`heating_circuits.yaml`**: Lattia- ja kattolämmityspiirien sekä sähköpatteriryhmien nimellistehot, vikapoikkeamien valvonta, vyöhykekohtaiset tavoitelämpötilat (kiinteä tai offset), aikataulut ja loma-asetukset.
- **`safety.yaml`**: Pääkeskuksen (esim. 3x25A) sekä mahdollisten erillisten ryhmäkeskusten (esim. autotalli tai pihakeskus) turvatehorajat (kW), ohitus- ja aikataulupoikkeukset (`overrides_and_schedules`) sekä loma-ajan ylläpito- ja paluudesinfiointisäännöt (`vacation_and_hygiene`).

Kun muokkaat profiilitiedostoja, voit ladata ne käyttöön ilman Home Assistantin uudelleenkäynnistystä ajamalla kehittäjätyökaluista palvelun `aisahkovahti.reload_profiles`.

---

## 🎛️ Ohjaustavat, Ohitukset ja Loma-/Ylläpitotila

Kaikki paketin automaatiopohjat ja apu-entiteetit tukevat seuraavia käyttäjän valittavissa olevia toimintoja:

- **Valittava ohjaustapa laite- ja automaatiokohtaisesti:**
  - *Halvat tunnit ja hintakatto*
  - *Vain aikataulu* (esim. yöaika `22:00–07:00`)
  - *Molemmat yhdessä (aikataulu + halvat tunnit)*
  - *Ei hinta- tai aikataulurajoitusta*
- **Ehdota → Hyväksy (`advisory_approve`) tai automaattinen ohjaus:** Järjestelmä voi pyytää puhelinilmoituksella hyväksynnän ennen lämmityksen tai varauksen käynnistämistä.
- **Käyttäjän välitön pakko-ohitus:** Mahdollistaa lämmityksen, akun latauksen tai sähköauton latauksen käynnistämisen heti myös kalliilla tunnilla tai aikataulun ulkopuolella (pääsulakesuoja pysyy silti aktiivisena).
- **Ohitettavat turvarajat:** Esimerkiksi lämminvesivaraajan minimilämpötilan tai kotiakuston UPS-reservirajan voi tilapäisesti ohittaa kalliiden hintapiikkien yli.
- **Vyöhykelämpötilat (kiinteä vs. ulkolämpötila + offset):** Huone- tai kerroskohtaiset tavoitelämpötilat voidaan asettaa joko kiinteiksi (esim. `21.0 °C` tai `17.0 °C`) tai seuraamaan ulkolämpötilaa säädettävällä erolla (esim. `ulkolämpötila + 2.0 °C`).
- **Loma- / ylläpitotila ja paluudesinfiointi:** Pudottaa valitut tilat ylläpitolämpötilaan (esim. `10 °C`) määritellyksi vuorokausiajaksi (esim. 30 vrk, maks. 180 vrk) ja voi sammuttaa lämminvesivaraajan loman ajaksi. Lomatilan päättyessä automaatio huolehtii tarvittaessa varaajan desinfiointiajosta (`+65 °C`) halvoilla tunneilla ennen normaaliin ohjaukseen palaamista.

---

## 🤖 Automaatiopohjien (Blueprints) käyttöönotto

Kun paketti on asennettu, voit luoda automaatiot valmiista pohjista kohdasta **Asetukset -> Automaatiot & Skriptit -> Blueprintit**:

1. **Älykäs Lämminvesivaraajan Ohjaus & Legionella-turva (`water_heater_smart_control.yaml`)**
  - Optimoi varaajan lämmityksen halvoille tunneille, hintakatolle tai aikataululle, noudattaa keskuksen turvatehorajaa ja tukee ohitettavaa `+55 °C` Legionella-suojaa, pakko-ohitusta sekä loma-ajan sammutusta ja paluudesinfiointia.
2. **Sähköauton Älylataus (`ev_smart_charging.yaml`)**
  - Käynnistää latauksen parhaina tunteina, hintakatolla tai aikataulussa aktiivisen autoprofiilin mukaisella virralla, tukee välitöntä pakko-ohitusta ja valvoo valitun pää- tai ryhmäkeskuksen (asunto tai erillinen autotalli) sulakerajaa.
3. **Rakenteiden Ennakoiva Esilämmitys & Vyöhyke-/Ylläpito-ohjaus (`thermal_mass_preheating.yaml`)**
  - Ohjaa vyöhykkeen lämpötilaa kiinteän tavoitteen tai `ulkolämpötila + offset` -laskennan mukaisesti huomioiden perus-, maksimi- ja mukavuusrajat, aikataulut, COP-pakkasrajan, hintapiikkivaroitukset sekä loma-/ylläpitotilan.
4. **Aurinkosähkön Ylijäämän & Halpojen Tuntien Ohjaus (`solar_excess_optimization.yaml`)**
  - Ohjaa ylijäämätuotannon lämminvesivaraajalle, laturille tai muille kuormille hystereesillä varustettuna, ja tukee rinnalla valinnaisia halpoja tunteja, aikataulua, pakko-ohitusta sekä kotiakuston minimirajan ohitusta.
5. **Kotiakuston & UPS-varavirran Älyohjaus (`battery_optimization.yaml`)**
  - Lataa kotiakustoa edullisina tunteina, hintakatolla tai aikataulussa sulakerajojen puitteissa, tukee pakkolatausohitusta ja purkaa akkua hintapiikkien aikana suojaten UPS-varavirtatason.

---

## 📞 Yhteystiedot ja Tuki

Onko sinulla kysyttävää, tarvitsetko apua asennuksessa tai haluatko keskustella kaupallisesta yhteistyöstä?

- **Sähköposti & Yhteydenotot:** `verkkohaukka@gmail.com`
- **Discord-yhteisö:** [https://discord.gg/SnBhsXpAW7](https://discord.gg/SnBhsXpAW7)
- **AI-Sähkövahti:** [https://aisahkovahti.65.109.171.178.sslip.io/](https://aisahkovahti.65.109.171.178.sslip.io/)

*AI-Sähkövahti / VerkkoHaukka® — Kaikki oikeudet pidätetään.*
