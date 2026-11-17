# ⚡ AI-Sähkövahti Home Assistant Integration (Pro & VIP)

Tervetuloa AI-Sähkövahdin viralliseen Home Assistant -integraatiopakettiin! Tämä paketti mahdollistaa sähkömarkkinoiden älykkään ohjauksen, hintojen ennakoinnin (Pro 7 vrk / VIP 30 vrk), sähköauton älylatauksen, kotiakuston ohjauksen, aurinkosähkön ylijäämän hyödyntämisen sekä talojen rakenteiden ennakoivan esilämmityksen turvallisesti.

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
