# ⚡ AI-Sähkövahti Home Assistant Integration (Pro & VIP)

Tervetuloa AI-Sähkövahdin viralliseen Home Assistant -integraatiopakettiin! Tämä paketti mahdollistaa sähkömarkkinoiden älykkään ohjauksen, hintojen ennakoinnin (Pro 7 vrk / VIP 30 vrk), dynaamiset laiteprofiilit sekä pää- ja ryhmäkeskuskohtaisen kuormanhallinnan turvallisesti.

---

## 🔒 Turvallisuus ja Lisenssi

Paketin käyttö vaatii voimassa olevan **Pro-** tai **VIP-jäsenyyden** (hankittavissa Gumroadista: [https://hawknet.gumroad.com/](https://hawknet.gumroad.com/)).

* **Palvelinvarmennettu lisenssi:** Asennuksen yhteydessä syötetään henkilökohtainen lisenssiavain. Palvelin tarkistaa tilauksen voimassaolon ja määrittää tilaustason (**Pro** tai **VIP**) automaattisesti. Tilausjakson päättyessä integraation käyttö keskeytyy, kunnes tilaus uusitaan.
* **Monitasoinen turvakerros:** Paketti sisältää sisäänrakennetun **Legionella-turvavahdin** (min. +55 °C), pää- ja ryhmäkeskuskohtaisen **sulakesuojan**, lämpöpumppujen **COP-pakkasrajan**, lämmityspiirien **vikadiagnostiikan** sekä kotiakuston **UPS-varavirtasuojan**.

---

## 📂 Tiedostorakenne (Repository Structure)

ZIP-paketti ja GitHub-repositorio noudattavat seuraavaa rakennetta:

```text
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
🚀 Asennusohjeet Home Assistantiin
1. Pura ZIP-paketti ja kopioi tiedostot
Lataa ZIP-paketti (tai kloonaa tämä repositorio) ja pura sen sisältö.

Kopioi seuraavat neljä kansiota suoraan Home Assistant -palvelimesi /config/-juurikansioon:

custom_components/aisahkovahti/

blueprints/automation/aisahkovahti/

device_profiles/

packages/

2. Ota packages-kansio käyttöön configuration.yaml-tiedostossa
Jotta dynaamiset autoprofiilit, keskusten turvatehorajat ja audit-loki latautuvat automaattisesti, varmista että Home Assistantin /config/configuration.yaml-tiedostossa on homeassistant:-lohkon alla seuraava rivi:

YAML
homeassistant:
  packages: !include_dir_named packages
(Jos tiedostossa on jo homeassistant:-otsikko, lisää vain rivi packages: !include_dir_named packages sen alle kahdella välilyönnillä sisennettynä.)

3. Käynnistä Home Assistant uudelleen ja lisää integraatio
Käynnistä Home Assistant uudelleen (Asetukset -> Järjestelmä -> Käynnistä uudelleen).

Mene kohtaan Asetukset (Settings) -> Laitteet ja palvelut (Devices & Services).

Klikkaa oikeasta alakulmasta Lisää integraatio (Add Integration) ja etsi listalta AI-Sähkövahti.

Syötä voimassa oleva lisenssiavaimesi. Integraatio tunnistaa tilaustasosi (PRO tai VIP) automaattisesti.

⚙️ Laiteprofiilit ja Ryhmäkeskukset (device_profiles/)
Voit räätälöidä kiinteistösi laitteet ja sulakerajat muokkaamalla /config/device_profiles/-kansion YAML-tiedostoja:

cars.yaml: Sähköautojen ja lataushybridien akkukapasiteetit (kWh), maksimivirrat (A) ja tavoitevaraukset (%).

heat_pumps.yaml: Ilmalämpöpumppujen (ILP) ja vesi-ilmalämpöpumppujen (VILP) vyöhykkeet ja COP-pakkasrajat.

heating_circuits.yaml: Lattia- ja kattolämmityspiirien nimellistehot ja vikapoikkeamien valvonta.

safety.yaml: Pääkeskuksen (esim. 3x25A) sekä mahdollisten erillisten ryhmäkeskusten (esim. autotalli tai pihakeskus) turvatehorajat (kW).

Kun muokkaat profiilitiedostoja, voit ladata ne käyttöön ilman Home Assistantin uudelleenkäynnistystä ajamalla kehittäjätyökaluista palvelun aisahkovahti.reload_profiles.

🤖 Automaatiopohjien (Blueprints) käyttöönotto
Kun paketti on asennettu, voit luoda automaatiot valmiista pohjista kohdasta Asetukset -> Automaatiot & Skriptit -> Blueprintit:

Älykäs Lämminvesivaraajan Ohjaus & Legionella-turva (water_heater_smart_control.yaml)

Optimoi varaajan lämmityksen halvoille tunneille, noudattaa senttihintakattoa ja keskuksen turvarajaa sekä varmistaa aina ehdottoman +55 °C Legionella-suojan.

Sähköauton Älylataus (ev_smart_charging.yaml)

Käynnistää latauksen parhaina tunteina aktiivisen autoprofiilin mukaisella virralla ja valvoo valitun pää- tai ryhmäkeskuksen (asunto tai erillinen autotalli) sulakerajaa.

Rakenteiden Ennakoiva Esilämmitys (thermal_mass_preheating.yaml)

Ohjaa vyöhykkeen lämpötilaa käyttäjän asettamien perus-, maksimi- ja mukavuusrajojen sekä senttihintakaton mukaisesti huomioiden COP-pakkasrajan ja hintapiikkivaroitukset.

Aurinkosähkön Ylijäämän Ohjaus (solar_excess_optimization.yaml)

Ohjaa ylijäämätuotannon lämminvesivaraajalle tai muille kuormille hystereesillä varustettuna, kun kotiakusto on saavuttanut tavoitetasonsa.

Kotiakuston & UPS-varavirran Älyohjaus (battery_optimization.yaml)

Lataa kotiakustoa edullisina tunteina sulakerajojen puitteissa ja purkaa akkua hintapiikkien aikana suojaten aina määritellyn UPS-varavirtatason.

📞 Yhteystiedot ja Tuki
Onko sinulla kysyttävää, tarvitsetko apua asennuksessa tai haluatko keskustella kaupallisesta yhteistyöstä?

Sähköposti & Yhteydenotot: verkkohaukka@gmail.com

Discord-yhteisö: https://discord.gg/SnBhsXpAW7

AI-Sähkövahti: https://aisahkovahti.65.109.171.178.sslip.io/

AI-Sähkövahti / VerkkoHaukka® — Kaikki oikeudet pidätetään.
