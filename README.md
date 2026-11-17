⚡ AI-Sähkövahti Home Assistant Integration (Pro & VIP)

Tervetuloa AI-Sähkövahdin viralliseen Home Assistant -integraatiopakettiin! Tämä paketti mahdollistaa sähkömarkkinoiden älykkään ohjauksen, hintojen ennakoinnin (Pro 7 vrk / VIP 30 vrk), sähköauton älylatauksen, kotiakuston ohjauksen sekä aurinkosähkön ylijäämän hyödyntämisen turvallisesti.

## 🔒 Turvallisuus ja Lisenssi
Paketin käyttö vaatii voimassa olevan **Pro-** tai **VIP-jäsenyyden** (hankittavissa Gumroadista: [https://hawknet.gumroad.com/](https://hawknet.gumroad.com/)). Asennuksen yhteydessä syötetään henkilökohtainen lisenssiavain, joka varmistaa suojatun yhteyden Hetzner-palvelimella pyöriviin ennustemalleihin.

Paketti sisältää sisäänrakennetun **Legionella-turvavahtilogiikan**, joka varmistaa, että lämminvesivaraajan lämpötila ei koskaan laske bakteeririskialueelle (min. +55 °C), vaikka sähkö olisi kuinka kautista tahansa.

---

## 📂 Tiedostorakenne (Repository Structure)

Varmista, että GitHub-repositoriossasi on seuraava rakenne:

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
└── README.md
```

---

## 🚀 Asennusohjeet Home Assistantiin

### Vaihtoehto A: Manuaalinen asennus
1. Lataa tämä repositorio tai kopioi sen tiedostot Home Assistant -palvelimesi `config/` -kansioon yllä olevan rakenteen mukaisesti.
2. Varmista, että kansiossa `custom_components/aisahkovahti/` sijaitsevat tiedostot:
  - `__init__.py`
  - `manifest.json`
  - `config_flow.py`
  - `sensor.py`
3. Varmista, että automaatiopohjat löytyvät kansiosta `config/blueprints/automation/aisahkovahti/`.
4. **Käynnistä Home Assistant uudelleen** (Settings -> System -> Restart).

### Vaihtoehto B: Integraation lisääminen asetuksista
1. Mene Home Assistantissa kohtaan **Asetukset (Settings)** -> **Laitteet ja palvelut (Devices & Services)**.
2. Klikkaa oikeasta alakulmasta **Lisää integraatio (Add Integration)**.
3. Etsi listalta **AI-Sähkövahti**.
4. Syötä pyydettäessä Gumroad-lisenssiavaimesi sekä valitse tilaustasosi (**Pro (7 vrk)** tai **VIP (30 vrk)**) ja maakunta-alueesi.

---

## 🤖 Automaatiopohjien (Blueprints) käyttöönotto

Kun paketti on asennettu, voit ottaa käyttöön neljä valmista automaatiota kohdasta **Asetukset -> Automaatiot & Skriptit -> Blueprintit**:

1. **Älykäs Lämminvesivaraajan Ohjaus & Legionella-turva**
  - Ottaa huomioon AI-Sähkövahdin parhaat tunnit, sisä- ja ulkolämpötilat sekä pitää huolen minimilämpötilasta.
2. **Sähköauton Älylataus**
  - Käynnistää latauksen yön edullisimmilla tunneilla ja keskeyttää sen hinnan noustessa.
3. **Kotiakuston Älyohjaus**
  - Lataa akkua halvoilla tunneilla ja suojaa kiinteistöä hintapiikeiltä.
4. **Aurinkosähkön Ylijäämän Ohjaus**
  - Ohjaa ylijäämätuotannon veden lämmitykseen tai muihin kuormiin, kun kotiakusto on täynnä.
5.- **Rakenteiden Ennakoiva Esilämmitys (Thermal Pre-heating)**
  - Lämmittää talon rakenteita (lattialämmitys tai ilmalämpöpumppu) +1–5 °C normaalia enemmän edullisina tunneina, hyödyntäen ennusteita tulevien kylmien jaksojen varalle.
---

## 📞 Yhteystiedot ja Tuki

Onko sinulla kysyttävää, tarvitsetko apua asennuksessa tai haluatko keskustella kaupallisesta yhteistyöstä?
- **Sähköposti & Yhteydenotot:** `verkkohaukka@gmail.com`
- **Discord-yhteisö:** [https://discord.gg/SnBhsXpAW7](https://discord.gg/SnBhsXpAW7)
- **AI-Sähkövahti:** https://aisahkovahti.65.109.171.178.sslip.io/

*AI-Sähkövahti / VerkkoHaukka® — Kaikki oikeudet pidätetään.*
