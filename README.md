# ⚡ AI-Sähkövahti Home Assistant Integration (Pro & VIP)

Tervetuloa AI-Sähkövahdin viralliseen Home Assistant -integraatiopakettiin! Tämä paketti mahdollistaa sähkömarkkinoiden älykkään ohjauksen, hintojen ennakoinnin (Pro 7 vrk / VIP 30 vrk), dynaamiset laiteprofiilit, joustavat aikataulu- ja ohitusvalinnat sekä pää- ja ryhmäkeskuskohtaisen kuormanhallinnan turvallisesti.

---

## 🔒 Turvallisuus ja Lisenssi

Paketin käyttö vaatii voimassa olevan **Pro-** tai **VIP-jäsenyyden** (hankittavissa Gumroadista: [https://hawknet.gumroad.com/](https://hawknet.gumroad.com/)).

- **Palvelinvarmennettu lisenssi:** Asennuksen yhteydessä syötetään henkilökohtainen lisenssiavain. Palvelin tarkistaa tilauksen voimassaolon ja määrittää tilaustason (**Pro** tai **VIP**) automaattisesti. Tilausjakson päättyessä integraation käyttö keskeytyy, kunnes tilaus uusitaan.
- **Monitasoinen turvakerros:** Paketti sisältää sisäänrakennetun **Legionella-turvavahdin** (min. +55 °C, tarvittaessa käyttäjän ohitettavissa), pää- ja ryhmäkeskuskohtaisen **sulakesuojan**, lämpöpumppujen **COP-pakkasrajan**, lämmityspiirien **vikadiagnostiikan**, kotiakuston **UPS-varavirtasuojan** sekä loman jälkeisen **paluudesinfioinnin**.

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
│   └── aisahkovahti_profiles.yaml
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
Jotta dynaamiset autoprofiilit, keskusten turvatehorajat, ohituskytkimet, loma-/ylläpitotilat ja audit-loki latautuvat automaattisesti, varmista että Home Assistantin `/config/configuration.yaml`-tiedostossa on `homeassistant:`-lohkon alla seuraava rivi:

~~~yaml
homeassistant:
  packages: !include_dir_named packages
~~~

*(Jos tiedostossa on jo `homeassistant:`-otsikko, lisää vain rivi `packages: !include_dir_named packages` sen alle kahdella välilyönnillä sisennettynä.)*

### 3. Käynnistä Home Assistant uudelleen ja lisää integraatio
1. Käynnistä Home Assistant uudelleen (**Asetukset -> Järjestelmä -> Käynnistä uudelleen**).
2. Mene kohtaan **Asetukset (Settings) -> Laitteet ja palvelut (Devices & Services)**.
3. Klikkaa oikeasta alakulmasta **Lisää integraatio (Add Integration)** ja etsi listalta **AI-Sähkövahti**.
4. Syötä voimassa oleva lisenssiavaimesi. Integraatio tunnistaa tilaustasosi (**PRO** tai **VIP**) automaattisesti.

---

## ⚙️ Laiteprofiilit ja Ryhmäkeskukset (`device_profiles/`)

Voit räätälöidä kiinteistösi laitteet, ohjaustavat, aikataulut, ohitukset ja sulakerajat muokkaamalla `/config/device_profiles/`-kansion YAML-tiedostoja:

- **`cars.yaml`**: Sähköautojen ja lataushybridien akkukapasiteetit (kWh), maksimivirrat (A), tavoitevaraukset (%), varakapasiteetit (`buffer_kwh`) sekä autokohtaiset lataussäännöt (`charging_rules`: halvat tunnit, hintakatto, aikataulut ja pakko-ohitus).
- **`heat_pumps.yaml`**: Ilmalämpöpumppujen (ILP) ja vesi-ilmalämpöpumppujen (VILP) vyöhykkeet, COP-pakkasrajat, lämpötilatavat (`temp_control`: kiinteä tavoite tai `ulkolämpötila + offset`) sekä loma-/ylläpitotilat (`operating_rules`).
- **`heating_circuits.yaml`**: Lattia- ja kattolämmityspiirien sekä sähköpatteriryhmien nimellistehot, vikapoikkeamien valvonta, vyöhykekohtaiset tavoitelämpötilat (kiinteä tai offset), aikataulut ja loma-asetukset.
- **`safety.yaml`**: Pääkeskuksen (esim. 3x25A) sekä mahdollisten erillisten ryhmäkeskusten (esim. autotalli tai pihakeskus) turvatehorajat (kW), ohitus- ja aikataulupoikkeukset (`overrides_and_schedules`) sekä loma-ajan ylläpito- ja paluudesinfiointisäännöt (`vacation_and_hygiene`).

Kun muokkaat profiilitiedostoja, voit ladata ne käyttöön ilman Home Assistantin uudelleenkäynnistystä ajamalla kehittäjätyökaluista palvelun `aisahkovahti.reload_profiles`.

---

## 🎛️ Ohjaustavat, Ohitukset ja Loma-/Ylläpitotila

Kaikki paketin automaatiopohjat ja apu-entiteetit (`packages/aisahkovahti_profiles.yaml`) tukevat seuraavia käyttäjän valittavissa olevia toimintoja:

- **Valittava ohjaustapa laite- ja automaatiokohtaisesti:**
  - *Halvat tunnit ja hintakatto*
  - *Vain aikataulu* (esim. yöaika `22:00–07:00`)
  - *Molemmat yhdessä (aikataulu + halvat tunnit)*
  - *Ei hinta- tai aikataulurajoitusta*
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
