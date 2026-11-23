from urllib.parse import urlencode
import uuid
import voluptuous as vol
import async_timeout
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

DOMAIN = "aisahkovahti"

YES_NO_OPTIONS = [
    {"value": "yes", "label": "Kyllä"},
    {"value": "no", "label": "Ei"},
]

TARIFF_TYPE_OPTIONS = [
    {
        "value": "spot",
        "label": "Pörssisähkö (tuntihinta — poimii vuorokauden halvimmat tunnit)",
    },
    {
        "value": "night_tariff",
        "label": "Yösähkö / Kausisähkö (halvempi yösähkö 22:00–07:00, usein vanha kontaktori)",
    },
    {
        "value": "fixed",
        "label": "Kiinteähintainen sopimus (pääsulakesuoja & kuormien porrastus)",
    },
]

FLOOR_SCOPE_OPTIONS = [
    {"value": "single", "label": "Yhdessä huoneessa / yhdellä alueella"},
    {"value": "multiple", "label": "Useammassa huoneessa / kerroksessa (lisätään peräkkäin)"},
]

SLAB_DEPTH_OPTIONS = [
    {"value": "deep_35_50mm", "label": "Syvä betonianturi (35–50 mm — varaava laatta)"},
    {"value": "shallow_or_near_pipe", "label": "Pinnassa tai lämpöputken lähellä"},
]

NORDPOOL_AREAS = [
    {"value": "FI", "label": "FI — Suomi / Finland (EUR)"},
    {"value": "SE1", "label": "SE1 — Ruotsi / Luleå (SEK / EUR)"},
    {"value": "SE2", "label": "SE2 — Ruotsi / Sundsvall (SEK / EUR)"},
    {"value": "SE3", "label": "SE3 — Ruotsi / Tukholma (SEK / EUR)"},
    {"value": "SE4", "label": "SE4 — Ruotsi / Malmö (SEK / EUR)"},
    {"value": "NO1", "label": "NO1 — Norja / Oslo (NOK / EUR)"},
    {"value": "NO2", "label": "NO2 — Norja / Kristiansand (NOK / EUR)"},
    {"value": "NO3", "label": "NO3 — Norja / Trondheim (NOK / EUR)"},
    {"value": "NO4", "label": "NO4 — Norja / Tromsø (NOK / EUR)"},
    {"value": "NO5", "label": "NO5 — Norja / Bergen (NOK / EUR)"},
    {"value": "DK1", "label": "DK1 — Tanska / Länsi (DKK / EUR)"},
    {"value": "DK2", "label": "DK2 — Tanska / Itä (DKK / EUR)"},
    {"value": "EE", "label": "EE — Viro / Estonia (EUR)"},
    {"value": "LV", "label": "LV — Latvia (EUR)"},
    {"value": "LT", "label": "LT — Liettua / Lithuania (EUR)"},
    {"value": "GER", "label": "GER / DE — Saksa / Germany (EUR)"},
    {"value": "AT", "label": "AT — Itävalta / Austria (EUR)"},
    {"value": "NL", "label": "NL — Alankomaat / Netherlands (EUR)"},
    {"value": "BE", "label": "BE — Belgia / Belgium (EUR)"},
    {"value": "FR", "label": "FR — Ranska / France (EUR)"},
    {"value": "PL", "label": "PL — Puola / Poland (PLN / EUR)"},
    {"value": "UK", "label": "UK — Iso-Britannia / Great Britain (GBP)"},
    {"value": "CH", "label": "CH — Sveitsi / Switzerland (CHF / EUR)"},
    {"value": "CZ", "label": "CZ — Tšekki / Czechia (CZK / EUR)"},
    {"value": "SK", "label": "SK — Slovakia (EUR)"},
    {"value": "HU", "label": "HU — Unkari / Hungary (HUF / EUR)"},
    {"value": "RO", "label": "RO — Romania (RON / EUR)"},
    {"value": "ES", "label": "ES — Espanja / Spain (EUR)"},
    {"value": "PT", "label": "PT — Portugali / Portugal (EUR)"},
    {"value": "IT", "label": "IT — Italia / Italy (EUR)"},
]

SUPPORTED_CURRENCIES = [
    {"value": "AUTO", "label": "AUTO — Automaattinen valitun maan mukaan"},
    {"value": "EUR", "label": "EUR (€ / c/kWh) — Euroalue (FI, EE, LV, LT, DE, AT, NL, BE, FR, SK, ES, PT, IT)"},
    {"value": "SEK", "label": "SEK (kr / öre/kWh) — Ruotsi / Sweden"},
    {"value": "NOK", "label": "NOK (kr / øre/kWh) — Norja / Norway"},
    {"value": "DKK", "label": "DKK (kr / øre/kWh) — Tanska / Denmark"},
    {"value": "PLN", "label": "PLN (zł / gr/kWh) — Puola / Poland"},
    {"value": "GBP", "label": "GBP (£ / p/kWh) — Iso-Britannia / UK"},
    {"value": "CHF", "label": "CHF (Fr. / Rp./kWh) — Sveitsi / Switzerland"},
    {"value": "CZK", "label": "CZK (Kč / hal./kWh) — Tšekki / Czechia"},
    {"value": "HUF", "label": "HUF (Ft/kWh) — Unkari / Hungary"},
    {"value": "RON", "label": "RON (lei / bani/kWh) — Romania"},
]

AREA_DEFAULT_CURRENCY = {
    "FI": "EUR",
    "SE1": "SEK", "SE2": "SEK", "SE3": "SEK", "SE4": "SEK",
    "NO1": "NOK", "NO2": "NOK", "NO3": "NOK", "NO4": "NOK", "NO5": "NOK",
    "DK1": "DKK", "DK2": "DKK",
    "EE": "EUR", "LV": "EUR", "LT": "EUR",
    "GER": "EUR", "DE": "EUR", "AT": "EUR", "NL": "EUR", "BE": "EUR", "FR": "EUR",
    "SK": "EUR", "ES": "EUR", "PT": "EUR", "IT": "EUR",
    "PL": "PLN",
    "UK": "GBP",
    "CH": "CHF",
    "CZ": "CZK",
    "HU": "HUF",
    "RO": "RON",
}

CURRENCY_SUBUNIT_MAP = {
    "EUR": "c/kWh",
    "SEK": "öre/kWh",
    "NOK": "øre/kWh",
    "DKK": "øre/kWh",
    "PLN": "gr/kWh",
    "GBP": "p/kWh",
    "CHF": "Rp./kWh",
    "CZK": "hal./kWh",
    "HUF": "Ft/kWh",
    "RON": "bani/kWh",
}

PRICE_SOURCE_MODES = [
    {"value": "server", "label": "AI-Sähkövahti API (Suomi / FI oletus)"},
    {"value": "ha_entity", "label": "Oma Home Assistant -hintasensori (Nord Pool / ENTSO-E / Tibber)"},
    {"value": "custom_api", "label": "Oma API-osoite (URL + valinnainen API-avain)"},
]

DEVICE_CATEGORIES = [
    {"value": "water_heater", "label": "Lämminvesivaraaja (Legionella-turvavahti +55°C)"},
    {"value": "floor_heating", "label": "Lattialämmitys (huone / kerros / betoni- tai pintalämpö)"},
    {"value": "heating_circuit", "label": "Sähköpatterit / Kattolämmitys (Yläkerta / Alakerta)"},
    {"value": "heat_pump", "label": "Ilmalämpöpumppu / Maalämpö / VILP (esim. Mitsubishi, NIBE)"},
    {"value": "ev_charger", "label": "Sähköauto tai latausasema (esim. Tesla, Easee, Zaptec)"},
    {"value": "sauna", "label": "Saunan kiuas / Suuri kertakuorma"},
    {"value": "other", "label": "Muu sähkölaitteisto / Kuorma"},
]

PANEL_GROUPS = [
    {"value": "pääkeskus", "label": "Pääkeskus (yleinen)"},
    {"value": "ryhmä_1_lämmitys", "label": "Ryhmä 1 — Lämmitys / Varaaja"},
    {"value": "ryhmä_2_auto_piha", "label": "Ryhmä 2 — Autotalli / Lataus"},
    {"value": "ryhmä_3_sauna_kodinhoito", "label": "Ryhmä 3 — Sauna / Kodinhoitohuone"},
]

OPTIONS_MENU_CHOICES = [
    {
        "value": "guided_wizard",
        "label": "Opastettu Kyllä / Ei -pika-asennus (Yösähkö/Pörssisähkö, Anturit, Varaaja, Lattialämmitys, Auto, Pumput)",
    },
    {
        "value": "add_device",
        "label": "Lisää yksittäinen laite tai huone (myös ilman nettiyhteyttä)",
    },
    {
        "value": "manage_devices",
        "label": "Hallitse tai poista lisättyjä laitteita (esim. auton vaihto)",
    },
    {
        "value": "general_settings",
        "label": "Perusasetukset (Lisenssiavain, Maa, Valuutta, Hintalähde)",
    },
]


def resolve_currency_and_unit(area: str, currency_choice: str) -> tuple[str, str]:
    """Palauttaa toteutuneen valuuttakoodin ja alayksikön (esim. SEK -> öre/kWh)."""
    choice = (currency_choice or "AUTO").strip().upper()
    if choice == "AUTO" or choice not in CURRENCY_SUBUNIT_MAP:
        resolved = AREA_DEFAULT_CURRENCY.get(area.upper(), "EUR")
    else:
        resolved = choice
    return resolved, CURRENCY_SUBUNIT_MAP.get(resolved, "c/kWh")


def _build_recommendations(devices: list[dict], sensors_cfg: dict) -> list[str]:
    """Luo käyttäjälle selkokieliset suositukset Kyllä/Ei-valintojen ja tariffityypin perusteella."""
    recs: list[str] = []
    tariff = sensors_cfg.get("tariff_type", "spot")

    if tariff == "night_tariff":
        recs.append(
            "Yösähkö / Kausisähkö valittu: kuormat suositellaan porrastettavaksi yöaikaan (22:00–07:00), "
            "jotta lämminvesivaraaja, lattialämmitys ja sähköauto eivät käynnisty samalla sekunnilla klo 22:00."
        )
    elif tariff == "fixed":
        recs.append(
            "Kiinteähintainen sähkösopimus valittu: painopiste on pääsulakkeen suojauksessa ja suurten kuormien porrastuksessa."
        )
    else:
        recs.append(
            "Pörssisähkö valittu: kuormat keskitetään vuorokauden edullisimmille tunneille sulakerajojen puitteissa."
        )

    upstairs_count = len(sensors_cfg.get("upstairs_entities", [])) + (
        1 if sensors_cfg.get("upstairs_wifi_names") else 0
    )
    downstairs_count = len(sensors_cfg.get("downstairs_entities", [])) + (
        1 if sensors_cfg.get("downstairs_wifi_names") else 0
    )
    has_outdoor = bool(
        sensors_cfg.get("outdoor_entities") or sensors_cfg.get("outdoor_wifi_names")
    )

    if upstairs_count or downstairs_count:
        recs.append(
            f"Sisäanturit käytössä (Yläkerta: {upstairs_count} kpl, Alakerta: {downstairs_count} kpl): "
            "lämmitys ohjataan kerroskohtaisesti niin, ettei huonelämpö laske liikaa kalliina tunteina."
        )
    else:
        recs.append(
            "Ei sisälämpötila-antureita: lämmitys ajastetaan turvallisesti halvoille tunneille ja aikataulun mukaan."
        )

    if has_outdoor:
        recs.append(
            "Ulkoinen lämpötila-anturi yhdistetty: pakkasvaikutus ja lämmitystuntien tarve lasketaan paikallisen ulkolämpötilan mukaan."
        )

    for dev in devices:
        cat = dev.get("category")
        name = dev.get("name", "Laite")
        kw = dev.get("power_kw", 0)
        has_wifi = bool(dev.get("has_wifi_or_ha"))
        control_id = (dev.get("control_entity_id") or "").strip()

        if cat == "water_heater":
            if has_wifi and control_id:
                recs.append(
                    f"{name} ({kw} kW): etäohjaus ({control_id}) aktivoitu. Suositus: lämmitys {dev.get('cheapest_hours_needed', 3)} halvimmalle tunnille + Legionella-turvavahti (+55 °C)."
                )
            else:
                recs.append(
                    f"{name} ({kw} kW): ei WiFi-/HA-ohjausta. Home Assistant ei katkaise 230/400 V virtaa ilman relettä/kontaktoria — "
                    "suositus: sähköasentaja voi kytkeä edullisen WiFi-releen (esim. Shelly Pro 1PM) ohjaamaan varaajan olemassa olevaa kontaktoria (+55 °C Legionella-turva)."
                )

        elif cat == "floor_heating":
            has_concrete = bool(dev.get("has_concrete_sensor"))
            has_surface = bool(dev.get("has_surface_sensor"))
            if has_concrete:
                recs.append(
                    f"Lattialämmitys '{name}' ({kw} kW): betonianturi käytössä — suositus: varaava esilämmitys halvimmille tunneille tai yösähkölle."
                )
            elif has_surface:
                recs.append(
                    f"Lattialämmitys '{name}' ({kw} kW): pintalämpötila-anturi käytössä — suositus: lyhyemmät, tasaiset lämmitysjaksot, jotta lattian pinta ei viilene."
                )
            else:
                recs.append(
                    f"Lattialämmitys '{name}' ({kw} kW): ei lattia-anturia — suositus: tasainen aikataulu- ja hintakatto-ohjaus."
                )

        elif cat == "ev_charger":
            if has_wifi and control_id:
                recs.append(
                    f"Sähköauto/laturi '{name}' ({kw} kW): ohjataan suoraan HA-rajapinnan kautta ({control_id}) ilman erillistä relettä."
                )
            else:
                recs.append(
                    f"Sähköauto/laturi '{name}' ({kw} kW): lisätty kuormanhallintaan ilman pilviyhteyttä — ajasta auton tai laturin oma ajastin halvimmille tunneille."
                )

        elif cat in ("heat_pump", "heating_circuit", "sauna"):
            mode_txt = (
                f"HA-ohjaus ({control_id})"
                if (has_wifi and control_id)
                else "manuaalinen / vaatii releen tai kontaktorin etäohjaukseen"
            )
            recs.append(
                f"{name} ({kw} kW): {mode_txt} — huomioitu ryhmäkeskuksen ({dev.get('panel_group', 'pääkeskus')}) sulakesuojassa."
            )

    return recs


def _build_config_schema(defaults: dict) -> vol.Schema:
    """Rakentaa perusasetuslomakkeen."""
    default_area = defaults.get("area", "FI")
    default_mode = defaults.get(
        "price_source_mode",
        "server" if default_area == "FI" else "ha_entity",
    )

    fields = {
        vol.Required("license_key", default=defaults.get("license_key", "")): str,
        vol.Required("area", default=default_area): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=NORDPOOL_AREAS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(
            "currency_choice", default=defaults.get("currency_choice", "AUTO")
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=SUPPORTED_CURRENCIES,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required("price_source_mode", default=default_mode): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=PRICE_SOURCE_MODES,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Optional(
            "source_entity_id",
            description={"suggested_value": defaults.get("source_entity_id")},
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="sensor")
        ),
        vol.Optional(
            "price_attribute",
            default=defaults.get("price_attribute", "auto"),
        ): str,
        vol.Optional(
            "price_multiplier",
            default=float(defaults.get("price_multiplier", 1.0)),
        ): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0.001,
                max=1000.0,
                step=0.001,
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
        vol.Optional(
            "custom_price_url",
            default=defaults.get("custom_price_url", ""),
        ): str,
        vol.Optional(
            "custom_api_key",
            default=defaults.get("custom_api_key", ""),
        ): str,
    }
    return vol.Schema(fields)


def _build_add_device_schema(defaults: dict | None = None) -> vol.Schema:
    """Helppo yksittäisen laitteen lisäyslomake (toimii myös ilman nettiyhteyttä)."""
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required("name", default=d.get("name", "")): str,
            vol.Required(
                "category", default=d.get("category", "water_heater")
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=DEVICE_CATEGORIES,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                "has_wifi_or_ha", default=d.get("has_wifi_or_ha", "no")
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=YES_NO_OPTIONS,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            vol.Required(
                "power_kw", default=float(d.get("power_kw", 2.0))
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.1,
                    max=50.0,
                    step=0.1,
                    unit_of_measurement="kW",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                "panel_group", default=d.get("panel_group", "pääkeskus")
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=PANEL_GROUPS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                "cheapest_hours_needed",
                default=int(d.get("cheapest_hours_needed", 3)),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=24,
                    step=1,
                    unit_of_measurement="h",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                "control_entity_id",
                description={"suggested_value": d.get("control_entity_id")},
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["switch", "climate", "water_heater", "number", "input_boolean"]
                )
            ),
            vol.Optional(
                "wifi_device_note",
                default=d.get("wifi_device_note", ""),
            ): str,
        }
    )


def _normalize_and_validate_input(user_input: dict, fallback: dict | None = None):
    """Yhtenäistää ja tarkistaa käyttäjän syötteet asennuksessa ja asetuksissa."""
    base = fallback or {}
    errors = {}

    license_key = user_input["license_key"].strip()
    area = user_input.get("area", base.get("area", "FI")).strip().upper()
    currency_choice = (user_input.get("currency_choice") or "AUTO").strip().upper()
    resolved_currency, price_unit = resolve_currency_and_unit(area, currency_choice)

    price_source_mode = user_input.get("price_source_mode", "server")
    source_entity_id = (user_input.get("source_entity_id") or "").strip()
    price_attribute = (user_input.get("price_attribute") or "auto").strip() or "auto"
    price_multiplier = float(user_input.get("price_multiplier", 1.0))
    custom_price_url = (user_input.get("custom_price_url") or "").strip()
    custom_api_key = (user_input.get("custom_api_key") or "").strip()

    if area != "FI" and price_source_mode == "server":
        if source_entity_id:
            price_source_mode = "ha_entity"
        elif custom_price_url:
            price_source_mode = "custom_api"
        else:
            errors["source_entity_id"] = "non_fi_requires_local_source"

    if price_source_mode == "ha_entity" and not source_entity_id:
        errors["source_entity_id"] = "missing_source_entity"
    elif price_source_mode == "custom_api" and not custom_price_url:
        errors["custom_price_url"] = "missing_custom_url"

    cleaned = {
        **base,
        "license_key": license_key,
        "area": area,
        "currency_choice": currency_choice,
        "currency": resolved_currency,
        "price_unit": price_unit,
        "price_source_mode": price_source_mode,
        "source_entity_id": source_entity_id,
        "price_attribute": price_attribute,
        "price_multiplier": price_multiplier,
        "custom_price_url": custom_price_url,
        "custom_api_key": custom_api_key,
    }
    return cleaned, errors


async def _verify_license_on_server(hass, license_key: str) -> dict:
    """Tarkistaa lisenssiavaimen voimassaolon ja maksullisen tason suoraan palvelimelta."""
    query = urlencode({"key": license_key})
    url = f"https://aisahkovahti.65.109.171.178.sslip.io/api/v1/verify?{query}"
    session = async_get_clientsession(hass)
    try:
        async with async_timeout.timeout(10):
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("active", False):
                        server_tier = str(data.get("tier", "pro")).lower()
                        if server_tier not in ("pro", "vip"):
                            server_tier = "pro"
                        return {"active": True, "tier": server_tier}
    except Exception:
        pass

    return {"active": False, "tier": None}


class AISahkovahtiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """AI-Sähkövahdin asennusvelho: lisenssitarkistus + opastettu Kyllä/Ei-kysely."""

    VERSION = 1

    def __init__(self) -> None:
        self._base_config: dict = {}
        self._wizard_sensors: dict = {}
        self._wizard_devices: list[dict] = []
        self._floor_scope: str = "single"

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Mahdollistaa laitteiden, antureiden, Kyllä/Ei-velhon ja perusasetusten muokkauksen."""
        return AISahkovahtiOptionsFlowHandler()

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            cleaned, errors = _normalize_and_validate_input(user_input)

            unique_key = f"{cleaned['license_key']}_{cleaned['area']}"
            await self.async_set_unique_id(unique_key)
            self._abort_if_unique_id_configured()

            if not errors:
                status = await _verify_license_on_server(self.hass, cleaned["license_key"])
                if status["active"]:
                    cleaned["tier"] = status["tier"]
                    self._base_config = cleaned
                    self._wizard_sensors = {}
                    self._wizard_devices = []
                    return await self.async_step_wiz_sensors_yn()
                errors["base"] = "invalid_license_key"

        return self.async_show_form(
            step_id="user",
            data_schema=_build_config_schema(user_input or {}),
            errors=errors,
        )

    # -------------------------------------------------------------------------
    # VAIHE 1: Sähkösopimustyyppi (yösähkö / pörssisähkö) & Lämpötila-anturit
    # -------------------------------------------------------------------------
    async def async_step_wiz_sensors_yn(self, user_input=None):
        """Kysyy sähkösopimustyypin ja Kyllä/Ei: onko antureita sisällä tai ulkona."""
        if user_input is not None:
            has_up = user_input.get("has_upstairs_sensor") == "yes"
            has_down = user_input.get("has_downstairs_sensor") == "yes"
            has_out = user_input.get("has_outdoor_sensor") == "yes"
            self._wizard_sensors = {
                "tariff_type": user_input.get("tariff_type", "spot"),
                "has_upstairs_sensor": has_up,
                "has_downstairs_sensor": has_down,
                "has_outdoor_sensor": has_out,
                "upstairs_entities": [],
                "upstairs_wifi_names": "",
                "downstairs_entities": [],
                "downstairs_wifi_names": "",
                "outdoor_entities": [],
                "outdoor_wifi_names": "",
            }
            if has_up or has_down or has_out:
                return await self.async_step_wiz_sensors_details()
            return await self.async_step_wiz_water_yn()

        schema = vol.Schema(
            {
                vol.Required("tariff_type", default="spot"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=TARIFF_TYPE_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("has_upstairs_sensor", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("has_downstairs_sensor", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("has_outdoor_sensor", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="wiz_sensors_yn", data_schema=schema)

    async def async_step_wiz_sensors_details(self, user_input=None):
        """Antureiden valinta (useampi mahdollinen) ja/tai WiFi-nimen syöttö."""
        if user_input is not None:
            self._wizard_sensors["upstairs_entities"] = list(
                user_input.get("upstairs_entities") or []
            )
            self._wizard_sensors["upstairs_wifi_names"] = (
                user_input.get("upstairs_wifi_names") or ""
            ).strip()
            self._wizard_sensors["downstairs_entities"] = list(
                user_input.get("downstairs_entities") or []
            )
            self._wizard_sensors["downstairs_wifi_names"] = (
                user_input.get("downstairs_wifi_names") or ""
            ).strip()
            self._wizard_sensors["outdoor_entities"] = list(
                user_input.get("outdoor_entities") or []
            )
            self._wizard_sensors["outdoor_wifi_names"] = (
                user_input.get("outdoor_wifi_names") or ""
            ).strip()
            return await self.async_step_wiz_water_yn()

        fields = {}
        if self._wizard_sensors.get("has_upstairs_sensor"):
            fields[vol.Optional("upstairs_entities", default=[])] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            )
            fields[vol.Optional("upstairs_wifi_names", default="")] = str

        if self._wizard_sensors.get("has_downstairs_sensor"):
            fields[vol.Optional("downstairs_entities", default=[])] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            )
            fields[vol.Optional("downstairs_wifi_names", default="")] = str

        if self._wizard_sensors.get("has_outdoor_sensor"):
            fields[vol.Optional("outdoor_entities", default=[])] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            )
            fields[vol.Optional("outdoor_wifi_names", default="")] = str

        return self.async_show_form(
            step_id="wiz_sensors_details",
            data_schema=vol.Schema(fields),
        )

    # -------------------------------------------------------------------------
    # VAIHE 2: Lämminvesivaraaja (Kyllä / Ei -> WiFi/valmistaja Kyllä/Ei -> teho)
    # -------------------------------------------------------------------------
    async def async_step_wiz_water_yn(self, user_input=None):
        """Kysyy Kyllä/Ei: onko kohteessa lämminvesivaraaja."""
        if user_input is not None:
            if user_input.get("has_water_heater") == "yes":
                return await self.async_step_wiz_water_details()
            return await self.async_step_wiz_floor_yn()

        schema = vol.Schema(
            {
                vol.Required("has_water_heater", default="yes"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="wiz_water_yn", data_schema=schema)

    async def async_step_wiz_water_details(self, user_input=None):
        """Lämminvesivaraajan tiedot (toimii myös ilman WiFi- tai valmistajayhteyttä)."""
        if user_input is not None:
            has_wifi = user_input.get("has_wifi_or_ha") == "yes"
            control_entity = (
                (user_input.get("control_entity_id") or "").strip() if has_wifi else ""
            )
            self._wizard_devices.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "name": (user_input.get("name") or "Lämminvesivaraaja").strip(),
                    "category": "water_heater",
                    "has_wifi_or_ha": has_wifi,
                    "power_kw": round(float(user_input.get("power_kw", 3.0)), 2),
                    "panel_group": user_input.get("panel_group", "ryhmä_1_lämmitys"),
                    "cheapest_hours_needed": int(
                        user_input.get("cheapest_hours_needed", 3)
                    ),
                    "control_entity_id": control_entity,
                    "wifi_device_note": (user_input.get("wifi_device_note") or "").strip(),
                    "connection_mode": "ha_entity" if control_entity else "manual_offline",
                }
            )
            return await self.async_step_wiz_floor_yn()

        schema = vol.Schema(
            {
                vol.Required("name", default="Lämminvesivaraaja"): str,
                vol.Required("has_wifi_or_ha", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("power_kw", default=3.0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.5,
                        max=30.0,
                        step=0.1,
                        unit_of_measurement="kW",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    "panel_group", default="ryhmä_1_lämmitys"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=PANEL_GROUPS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "cheapest_hours_needed", default=3
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional("control_entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["switch", "water_heater", "input_boolean"]
                    )
                ),
                vol.Optional("wifi_device_note", default=""): str,
            }
        )
        return self.async_show_form(step_id="wiz_water_details", data_schema=schema)

    # -------------------------------------------------------------------------
    # VAIHE 3: Lattialämmitys (Kyllä/Ei -> 1 vai useampi huone -> betoni/pinta)
    # -------------------------------------------------------------------------
    async def async_step_wiz_floor_yn(self, user_input=None):
        """Kysyy Kyllä/Ei: onko lattialämmitystä (ja onko yhdessä vai useammassa huoneessa)."""
        if user_input is not None:
            if user_input.get("has_floor_heating") == "yes":
                self._floor_scope = user_input.get("floor_scope", "single")
                return await self.async_step_wiz_floor_room()
            return await self.async_step_wiz_ev_yn()

        schema = vol.Schema(
            {
                vol.Required("has_floor_heating", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("floor_scope", default="single"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=FLOOR_SCOPE_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="wiz_floor_yn", data_schema=schema)

    async def async_step_wiz_floor_room(self, user_input=None):
        """Lattialämmityshuoneen tiedot: huoneen nimi, teho, betonianturi, pintalämpötila."""
        if user_input is not None:
            has_wifi = user_input.get("has_wifi_or_ha") == "yes"
            has_concrete = user_input.get("has_concrete_sensor") == "yes"
            has_surface = user_input.get("has_surface_sensor") == "yes"
            control_entity = (
                (user_input.get("control_entity_id") or "").strip() if has_wifi else ""
            )
            self._wizard_devices.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "name": (user_input.get("room_name") or "Lattialämmitys").strip(),
                    "category": "floor_heating",
                    "has_wifi_or_ha": has_wifi,
                    "power_kw": round(float(user_input.get("power_kw", 1.5)), 2),
                    "panel_group": user_input.get("panel_group", "ryhmä_1_lämmitys"),
                    "cheapest_hours_needed": int(
                        user_input.get("cheapest_hours_needed", 4 if has_concrete else 6)
                    ),
                    "has_concrete_sensor": has_concrete,
                    "slab_sensor_depth": (
                        user_input.get("slab_sensor_depth", "deep_35_50mm")
                        if has_concrete
                        else "none"
                    ),
                    "has_surface_sensor": has_surface,
                    "floor_temp_entity_id": (
                        user_input.get("floor_temp_entity_id") or ""
                    ).strip(),
                    "control_entity_id": control_entity,
                    "connection_mode": "ha_entity" if control_entity else "manual_offline",
                }
            )
            if (
                self._floor_scope == "multiple"
                and user_input.get("add_another_room") == "yes"
            ):
                return await self.async_step_wiz_floor_room()
            return await self.async_step_wiz_ev_yn()

        fields = {
            vol.Required("room_name", default="Kylpyhuone"): str,
            vol.Required("power_kw", default=1.5): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.1,
                    max=30.0,
                    step=0.1,
                    unit_of_measurement="kW",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required("has_wifi_or_ha", default="no"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=YES_NO_OPTIONS,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            vol.Required("has_concrete_sensor", default="no"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=YES_NO_OPTIONS,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            vol.Required(
                "slab_sensor_depth", default="deep_35_50mm"
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SLAB_DEPTH_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required("has_surface_sensor", default="no"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=YES_NO_OPTIONS,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            vol.Optional("floor_temp_entity_id"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional("control_entity_id"): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["switch", "climate", "input_boolean"]
                )
            ),
            vol.Required(
                "panel_group", default="ryhmä_1_lämmitys"
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=PANEL_GROUPS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
        if self._floor_scope == "multiple":
            fields[
                vol.Required("add_another_room", default="no")
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=YES_NO_OPTIONS,
                    mode=selector.SelectSelectorMode.LIST,
                )
            )

        return self.async_show_form(
            step_id="wiz_floor_room",
            data_schema=vol.Schema(fields),
        )

    # -------------------------------------------------------------------------
    # VAIHE 4: Sähköauto tai latausasema (Kyllä / Ei + useampi auto mahdollinen)
    # -------------------------------------------------------------------------
    async def async_step_wiz_ev_yn(self, user_input=None):
        """Kysyy Kyllä/Ei: onko sähköauto tai latausasema."""
        if user_input is not None:
            if user_input.get("has_ev") == "yes":
                return await self.async_step_wiz_ev_details()
            return await self.async_step_wiz_other_yn()

        schema = vol.Schema(
            {
                vol.Required("has_ev", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="wiz_ev_yn", data_schema=schema)

    async def async_step_wiz_ev_details(self, user_input=None):
        """Sähköauton / laturin tiedot (helppo vaihtaa ja lisätä useampia autoja)."""
        if user_input is not None:
            has_wifi = user_input.get("has_wifi_or_ha") == "yes"
            control_entity = (
                (user_input.get("control_entity_id") or "").strip() if has_wifi else ""
            )
            self._wizard_devices.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "name": (user_input.get("name") or "Sähköauto").strip(),
                    "category": "ev_charger",
                    "has_wifi_or_ha": has_wifi,
                    "power_kw": round(float(user_input.get("power_kw", 11.0)), 2),
                    "panel_group": user_input.get("panel_group", "ryhmä_2_auto_piha"),
                    "cheapest_hours_needed": int(
                        user_input.get("cheapest_hours_needed", 4)
                    ),
                    "control_entity_id": control_entity,
                    "wifi_device_note": (user_input.get("wifi_device_note") or "").strip(),
                    "connection_mode": "ha_entity" if control_entity else "manual_offline",
                }
            )
            if user_input.get("add_another_ev") == "yes":
                return await self.async_step_wiz_ev_details()
            return await self.async_step_wiz_other_yn()

        schema = vol.Schema(
            {
                vol.Required("name", default="Sähköauto / Latausasema"): str,
                vol.Required("has_wifi_or_ha", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("power_kw", default=11.0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1.4,
                        max=22.0,
                        step=0.1,
                        unit_of_measurement="kW",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    "panel_group", default="ryhmä_2_auto_piha"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=PANEL_GROUPS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "cheapest_hours_needed", default=4
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional("control_entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["switch", "number", "input_boolean"]
                    )
                ),
                vol.Optional("wifi_device_note", default=""): str,
                vol.Required("add_another_ev", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="wiz_ev_details", data_schema=schema)

    # -------------------------------------------------------------------------
    # VAIHE 5: Muut laitteet (ILP, sähköpatterit, sauna) & viimeistely
    # -------------------------------------------------------------------------
    async def async_step_wiz_other_yn(self, user_input=None):
        """Kysyy Kyllä/Ei: lisätäänkö ilmalämpöpumppu, sähköpatterit tai sauna."""
        if user_input is not None:
            if user_input.get("has_other_device") == "yes":
                return await self.async_step_wiz_other_details()
            return await self._finish_wizard()

        schema = vol.Schema(
            {
                vol.Required("has_other_device", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="wiz_other_yn", data_schema=schema)

    async def async_step_wiz_other_details(self, user_input=None):
        """Ilmalämpöpumpun, sähköpatterien tai saunan lisäys."""
        if user_input is not None:
            has_wifi = user_input.get("has_wifi_or_ha") == "yes"
            control_entity = (
                (user_input.get("control_entity_id") or "").strip() if has_wifi else ""
            )
            self._wizard_devices.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "name": (user_input.get("name") or "Lämmityslaite").strip(),
                    "category": user_input.get("category", "heat_pump"),
                    "has_wifi_or_ha": has_wifi,
                    "power_kw": round(float(user_input.get("power_kw", 2.0)), 2),
                    "panel_group": user_input.get("panel_group", "pääkeskus"),
                    "cheapest_hours_needed": int(
                        user_input.get("cheapest_hours_needed", 3)
                    ),
                    "control_entity_id": control_entity,
                    "wifi_device_note": (user_input.get("wifi_device_note") or "").strip(),
                    "connection_mode": "ha_entity" if control_entity else "manual_offline",
                }
            )
            if user_input.get("add_more_other") == "yes":
                return await self.async_step_wiz_other_details()
            return await self._finish_wizard()

        schema = vol.Schema(
            {
                vol.Required(
                    "category", default="heat_pump"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {
                                "value": "heat_pump",
                                "label": "Ilmalämpöpumppu / VILP / Maalämpö (esim. Mitsubishi, NIBE)",
                            },
                            {
                                "value": "heating_circuit",
                                "label": "Sähköpatterit (Yläkerta / Alakerta)",
                            },
                            {
                                "value": "sauna",
                                "label": "Saunan kiuas / Suuri kertakuorma",
                            },
                            {"value": "other", "label": "Muu sähkölaitteisto"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required("name", default="Ilmalämpöpumppu"): str,
                vol.Required("has_wifi_or_ha", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("power_kw", default=2.0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        max=30.0,
                        step=0.1,
                        unit_of_measurement="kW",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required("panel_group", default="pääkeskus"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=PANEL_GROUPS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "cheapest_hours_needed", default=3
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional("control_entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["switch", "climate", "water_heater", "input_boolean"]
                    )
                ),
                vol.Optional("wifi_device_note", default=""): str,
                vol.Required("add_more_other", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="wiz_other_details", data_schema=schema)

    async def _finish_wizard(self):
        """Tallentaa valinnat ja automaattisesti luodut suositukset."""
        final_data = dict(self._base_config)
        final_data["ui_devices"] = list(self._wizard_devices)
        final_data["temperature_sensors"] = dict(self._wizard_sensors)
        final_data["wizard_recommendations"] = _build_recommendations(
            self._wizard_devices, self._wizard_sensors
        )
        tier_upper = str(final_data.get("tier", "pro")).upper()
        return self.async_create_entry(
            title=f"AI-Sähkövahti {final_data['area']} [{final_data['currency']}] ({tier_upper})",
            data=final_data,
        )


class AISahkovahtiOptionsFlowHandler(config_entries.OptionsFlow):
    """Graafinen hallintavalikko: Kyllä/Ei-pika-asennus, yksittäinen lisäys, poisto ja asetukset."""

    def __init__(self) -> None:
        self._wizard_sensors: dict = {}
        self._wizard_devices: list[dict] = []
        self._floor_scope: str = "single"

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            action = user_input.get("menu_action")
            if action == "guided_wizard":
                self._wizard_sensors = {}
                self._wizard_devices = []
                return await self.async_step_wiz_sensors_yn()
            if action == "add_device":
                return await self.async_step_add_device()
            if action == "manage_devices":
                return await self.async_step_manage_devices()
            return await self.async_step_general_settings()

        devices = list(self.config_entry.data.get("ui_devices", []))
        schema = vol.Schema(
            {
                vol.Required("menu_action", default="guided_wizard"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=OPTIONS_MENU_CHOICES,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={"device_count": str(len(devices))},
        )

    async def async_step_wiz_sensors_yn(self, user_input=None):
        if user_input is not None:
            has_up = user_input.get("has_upstairs_sensor") == "yes"
            has_down = user_input.get("has_downstairs_sensor") == "yes"
            has_out = user_input.get("has_outdoor_sensor") == "yes"
            self._wizard_sensors = {
                "tariff_type": user_input.get("tariff_type", "spot"),
                "has_upstairs_sensor": has_up,
                "has_downstairs_sensor": has_down,
                "has_outdoor_sensor": has_out,
                "upstairs_entities": [],
                "upstairs_wifi_names": "",
                "downstairs_entities": [],
                "downstairs_wifi_names": "",
                "outdoor_entities": [],
                "outdoor_wifi_names": "",
            }
            if has_up or has_down or has_out:
                return await self.async_step_wiz_sensors_details()
            return await self.async_step_wiz_water_yn()

        schema = vol.Schema(
            {
                vol.Required("tariff_type", default="spot"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=TARIFF_TYPE_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("has_upstairs_sensor", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("has_downstairs_sensor", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("has_outdoor_sensor", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="wiz_sensors_yn", data_schema=schema)

    async def async_step_wiz_sensors_details(self, user_input=None):
        if user_input is not None:
            self._wizard_sensors["upstairs_entities"] = list(
                user_input.get("upstairs_entities") or []
            )
            self._wizard_sensors["upstairs_wifi_names"] = (
                user_input.get("upstairs_wifi_names") or ""
            ).strip()
            self._wizard_sensors["downstairs_entities"] = list(
                user_input.get("downstairs_entities") or []
            )
            self._wizard_sensors["downstairs_wifi_names"] = (
                user_input.get("downstairs_wifi_names") or ""
            ).strip()
            self._wizard_sensors["outdoor_entities"] = list(
                user_input.get("outdoor_entities") or []
            )
            self._wizard_sensors["outdoor_wifi_names"] = (
                user_input.get("outdoor_wifi_names") or ""
            ).strip()
            return await self.async_step_wiz_water_yn()

        fields = {}
        if self._wizard_sensors.get("has_upstairs_sensor"):
            fields[vol.Optional("upstairs_entities", default=[])] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            )
            fields[vol.Optional("upstairs_wifi_names", default="")] = str

        if self._wizard_sensors.get("has_downstairs_sensor"):
            fields[vol.Optional("downstairs_entities", default=[])] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            )
            fields[vol.Optional("downstairs_wifi_names", default="")] = str

        if self._wizard_sensors.get("has_outdoor_sensor"):
            fields[vol.Optional("outdoor_entities", default=[])] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", multiple=True)
            )
            fields[vol.Optional("outdoor_wifi_names", default="")] = str

        return self.async_show_form(
            step_id="wiz_sensors_details",
            data_schema=vol.Schema(fields),
        )

    async def async_step_wiz_water_yn(self, user_input=None):
        if user_input is not None:
            if user_input.get("has_water_heater") == "yes":
                return await self.async_step_wiz_water_details()
            return await self.async_step_wiz_floor_yn()

        schema = vol.Schema(
            {
                vol.Required("has_water_heater", default="yes"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="wiz_water_yn", data_schema=schema)

    async def async_step_wiz_water_details(self, user_input=None):
        if user_input is not None:
            has_wifi = user_input.get("has_wifi_or_ha") == "yes"
            control_entity = (
                (user_input.get("control_entity_id") or "").strip() if has_wifi else ""
            )
            self._wizard_devices.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "name": (user_input.get("name") or "Lämminvesivaraaja").strip(),
                    "category": "water_heater",
                    "has_wifi_or_ha": has_wifi,
                    "power_kw": round(float(user_input.get("power_kw", 3.0)), 2),
                    "panel_group": user_input.get("panel_group", "ryhmä_1_lämmitys"),
                    "cheapest_hours_needed": int(
                        user_input.get("cheapest_hours_needed", 3)
                    ),
                    "control_entity_id": control_entity,
                    "wifi_device_note": (user_input.get("wifi_device_note") or "").strip(),
                    "connection_mode": "ha_entity" if control_entity else "manual_offline",
                }
            )
            return await self.async_step_wiz_floor_yn()

        schema = vol.Schema(
            {
                vol.Required("name", default="Lämminvesivaraaja"): str,
                vol.Required("has_wifi_or_ha", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("power_kw", default=3.0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.5,
                        max=30.0,
                        step=0.1,
                        unit_of_measurement="kW",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    "panel_group", default="ryhmä_1_lämmitys"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=PANEL_GROUPS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "cheapest_hours_needed", default=3
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional("control_entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["switch", "water_heater", "input_boolean"]
                    )
                ),
                vol.Optional("wifi_device_note", default=""): str,
            }
        )
        return self.async_show_form(step_id="wiz_water_details", data_schema=schema)

    async def async_step_wiz_floor_yn(self, user_input=None):
        if user_input is not None:
            if user_input.get("has_floor_heating") == "yes":
                self._floor_scope = user_input.get("floor_scope", "single")
                return await self.async_step_wiz_floor_room()
            return await self.async_step_wiz_ev_yn()

        schema = vol.Schema(
            {
                vol.Required("has_floor_heating", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("floor_scope", default="single"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=FLOOR_SCOPE_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="wiz_floor_yn", data_schema=schema)

    async def async_step_wiz_floor_room(self, user_input=None):
        if user_input is not None:
            has_wifi = user_input.get("has_wifi_or_ha") == "yes"
            has_concrete = user_input.get("has_concrete_sensor") == "yes"
            has_surface = user_input.get("has_surface_sensor") == "yes"
            control_entity = (
                (user_input.get("control_entity_id") or "").strip() if has_wifi else ""
            )
            self._wizard_devices.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "name": (user_input.get("room_name") or "Lattialämmitys").strip(),
                    "category": "floor_heating",
                    "has_wifi_or_ha": has_wifi,
                    "power_kw": round(float(user_input.get("power_kw", 1.5)), 2),
                    "panel_group": user_input.get("panel_group", "ryhmä_1_lämmitys"),
                    "cheapest_hours_needed": int(
                        user_input.get("cheapest_hours_needed", 4 if has_concrete else 6)
                    ),
                    "has_concrete_sensor": has_concrete,
                    "slab_sensor_depth": (
                        user_input.get("slab_sensor_depth", "deep_35_50mm")
                        if has_concrete
                        else "none"
                    ),
                    "has_surface_sensor": has_surface,
                    "floor_temp_entity_id": (
                        user_input.get("floor_temp_entity_id") or ""
                    ).strip(),
                    "control_entity_id": control_entity,
                    "connection_mode": "ha_entity" if control_entity else "manual_offline",
                }
            )
            if (
                self._floor_scope == "multiple"
                and user_input.get("add_another_room") == "yes"
            ):
                return await self.async_step_wiz_floor_room()
            return await self.async_step_wiz_ev_yn()

        fields = {
            vol.Required("room_name", default="Kylpyhuone"): str,
            vol.Required("power_kw", default=1.5): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.1,
                    max=30.0,
                    step=0.1,
                    unit_of_measurement="kW",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required("has_wifi_or_ha", default="no"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=YES_NO_OPTIONS,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            vol.Required("has_concrete_sensor", default="no"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=YES_NO_OPTIONS,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            vol.Required(
                "slab_sensor_depth", default="deep_35_50mm"
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SLAB_DEPTH_OPTIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required("has_surface_sensor", default="no"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=YES_NO_OPTIONS,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            vol.Optional("floor_temp_entity_id"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            vol.Optional("control_entity_id"): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain=["switch", "climate", "input_boolean"]
                )
            ),
            vol.Required(
                "panel_group", default="ryhmä_1_lämmitys"
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=PANEL_GROUPS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        }
        if self._floor_scope == "multiple":
            fields[
                vol.Required("add_another_room", default="no")
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=YES_NO_OPTIONS,
                    mode=selector.SelectSelectorMode.LIST,
                )
            )

        return self.async_show_form(
            step_id="wiz_floor_room",
            data_schema=vol.Schema(fields),
        )

    async def async_step_wiz_ev_yn(self, user_input=None):
        if user_input is not None:
            if user_input.get("has_ev") == "yes":
                return await self.async_step_wiz_ev_details()
            return await self.async_step_wiz_other_yn()

        schema = vol.Schema(
            {
                vol.Required("has_ev", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="wiz_ev_yn", data_schema=schema)

    async def async_step_wiz_ev_details(self, user_input=None):
        if user_input is not None:
            has_wifi = user_input.get("has_wifi_or_ha") == "yes"
            control_entity = (
                (user_input.get("control_entity_id") or "").strip() if has_wifi else ""
            )
            self._wizard_devices.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "name": (user_input.get("name") or "Sähköauto").strip(),
                    "category": "ev_charger",
                    "has_wifi_or_ha": has_wifi,
                    "power_kw": round(float(user_input.get("power_kw", 11.0)), 2),
                    "panel_group": user_input.get("panel_group", "ryhmä_2_auto_piha"),
                    "cheapest_hours_needed": int(
                        user_input.get("cheapest_hours_needed", 4)
                    ),
                    "control_entity_id": control_entity,
                    "wifi_device_note": (user_input.get("wifi_device_note") or "").strip(),
                    "connection_mode": "ha_entity" if control_entity else "manual_offline",
                }
            )
            if user_input.get("add_another_ev") == "yes":
                return await self.async_step_wiz_ev_details()
            return await self.async_step_wiz_other_yn()

        schema = vol.Schema(
            {
                vol.Required("name", default="Sähköauto / Latausasema"): str,
                vol.Required("has_wifi_or_ha", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("power_kw", default=11.0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1.4,
                        max=22.0,
                        step=0.1,
                        unit_of_measurement="kW",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    "panel_group", default="ryhmä_2_auto_piha"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=PANEL_GROUPS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "cheapest_hours_needed", default=4
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional("control_entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["switch", "number", "input_boolean"]
                    )
                ),
                vol.Optional("wifi_device_note", default=""): str,
                vol.Required("add_another_ev", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="wiz_ev_details", data_schema=schema)

    async def async_step_wiz_other_yn(self, user_input=None):
        if user_input is not None:
            if user_input.get("has_other_device") == "yes":
                return await self.async_step_wiz_other_details()
            return await self._finish_options_wizard()

        schema = vol.Schema(
            {
                vol.Required("has_other_device", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="wiz_other_yn", data_schema=schema)

    async def async_step_wiz_other_details(self, user_input=None):
        if user_input is not None:
            has_wifi = user_input.get("has_wifi_or_ha") == "yes"
            control_entity = (
                (user_input.get("control_entity_id") or "").strip() if has_wifi else ""
            )
            self._wizard_devices.append(
                {
                    "id": uuid.uuid4().hex[:8],
                    "name": (user_input.get("name") or "Lämmityslaite").strip(),
                    "category": user_input.get("category", "heat_pump"),
                    "has_wifi_or_ha": has_wifi,
                    "power_kw": round(float(user_input.get("power_kw", 2.0)), 2),
                    "panel_group": user_input.get("panel_group", "pääkeskus"),
                    "cheapest_hours_needed": int(
                        user_input.get("cheapest_hours_needed", 3)
                    ),
                    "control_entity_id": control_entity,
                    "wifi_device_note": (user_input.get("wifi_device_note") or "").strip(),
                    "connection_mode": "ha_entity" if control_entity else "manual_offline",
                }
            )
            if user_input.get("add_more_other") == "yes":
                return await self.async_step_wiz_other_details()
            return await self._finish_options_wizard()

        schema = vol.Schema(
            {
                vol.Required(
                    "category", default="heat_pump"
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {
                                "value": "heat_pump",
                                "label": "Ilmalämpöpumppu / VILP / Maalämpö (esim. Mitsubishi, NIBE)",
                            },
                            {
                                "value": "heating_circuit",
                                "label": "Sähköpatterit (Yläkerta / Alakerta)",
                            },
                            {
                                "value": "sauna",
                                "label": "Saunan kiuas / Suuri kertakuorma",
                            },
                            {"value": "other", "label": "Muu sähkölaitteisto"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required("name", default="Ilmalämpöpumppu"): str,
                vol.Required("has_wifi_or_ha", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
                vol.Required("power_kw", default=2.0): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.1,
                        max=30.0,
                        step=0.1,
                        unit_of_measurement="kW",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required("panel_group", default="pääkeskus"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=PANEL_GROUPS,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    "cheapest_hours_needed", default=3
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=24,
                        step=1,
                        unit_of_measurement="h",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional("control_entity_id"): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["switch", "climate", "water_heater", "input_boolean"]
                    )
                ),
                vol.Optional("wifi_device_note", default=""): str,
                vol.Required("add_more_other", default="no"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=YES_NO_OPTIONS,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="wiz_other_details", data_schema=schema)

    async def _finish_options_wizard(self):
        updated = dict(self.config_entry.data)
        updated["ui_devices"] = list(self._wizard_devices)
        updated["temperature_sensors"] = dict(self._wizard_sensors)
        updated["wizard_recommendations"] = _build_recommendations(
            self._wizard_devices, self._wizard_sensors
        )
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=updated,
        )
        await self.hass.config_entries.async_reload(self.config_entry.entry_id)
        return self.async_create_entry(title="", data={})

    async def async_step_add_device(self, user_input=None):
        """Lisää yksittäisen ohjattavan laitteen (toimii myös ilman nettiyhteyttä)."""
        errors = {}
        if user_input is not None:
            name = (user_input.get("name") or "").strip()
            if not name:
                errors["name"] = "missing_device_name"
            else:
                has_wifi = user_input.get("has_wifi_or_ha") == "yes"
                control_entity = (
                    (user_input.get("control_entity_id") or "").strip()
                    if has_wifi
                    else ""
                )
                new_device = {
                    "id": uuid.uuid4().hex[:8],
                    "name": name,
                    "category": user_input.get("category", "other"),
                    "has_wifi_or_ha": has_wifi,
                    "power_kw": round(float(user_input.get("power_kw", 2.0)), 2),
                    "panel_group": user_input.get("panel_group", "pääkeskus"),
                    "cheapest_hours_needed": int(
                        user_input.get("cheapest_hours_needed", 3)
                    ),
                    "control_entity_id": control_entity,
                    "wifi_device_note": (user_input.get("wifi_device_note") or "").strip(),
                    "connection_mode": "ha_entity" if control_entity else "manual_offline",
                }
                updated = dict(self.config_entry.data)
                devices = list(updated.get("ui_devices", []))
                devices.append(new_device)
                updated["ui_devices"] = devices
                updated["wizard_recommendations"] = _build_recommendations(
                    devices, dict(updated.get("temperature_sensors", {}))
                )

                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=updated,
                )
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="add_device",
            data_schema=_build_add_device_schema(user_input),
            errors=errors,
        )

    async def async_step_manage_devices(self, user_input=None):
        """Mahdollistaa lisättyjen laitteiden tarkastelun ja poistamisen yhdellä klikkauksella."""
        updated = dict(self.config_entry.data)
        devices = list(updated.get("ui_devices", []))

        if not devices:
            return await self.async_step_add_device()

        if user_input is not None:
            to_remove = set(user_input.get("remove_ids") or [])
            if to_remove:
                remaining = [d for d in devices if d.get("id") not in to_remove]
                updated["ui_devices"] = remaining
                updated["wizard_recommendations"] = _build_recommendations(
                    remaining, dict(updated.get("temperature_sensors", {}))
                )
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=updated,
                )
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        options = []
        for d in devices:
            conn_label = (
                f"HA: {d['control_entity_id']}"
                if d.get("control_entity_id")
                else "Manuaalinen / Ei WiFi-yhteyttä"
            )
            options.append(
                {
                    "value": d["id"],
                    "label": f"{d['name']} ({d['power_kw']} kW, {d['panel_group']} — {conn_label})",
                }
            )

        schema = vol.Schema(
            {
                vol.Optional("remove_ids", default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="manage_devices",
            data_schema=schema,
        )

    async def async_step_general_settings(self, user_input=None):
        """Perusasetusten muokkaus."""
        errors = {}
        current = dict(self.config_entry.data)

        if user_input is not None:
            cleaned, errors = _normalize_and_validate_input(user_input, fallback=current)

            if not errors:
                status = await _verify_license_on_server(self.hass, cleaned["license_key"])
                if status["active"]:
                    verified_tier = status["tier"]
                    cleaned["tier"] = verified_tier
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        title=f"AI-Sähkövahti {cleaned['area']} [{cleaned['currency']}] ({verified_tier.upper()})",
                        data=cleaned,
                    )
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                    return self.async_create_entry(title="", data={})
                errors["base"] = "invalid_license_key"

        return self.async_show_form(
            step_id="general_settings",
            data_schema=_build_config_schema(user_input or current),
            errors=errors,
        )
