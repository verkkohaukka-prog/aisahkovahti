from urllib.parse import urlencode
import voluptuous as vol
import async_timeout
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

DOMAIN = "aisahkovahti"

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


def resolve_currency_and_unit(area: str, currency_choice: str) -> tuple[str, str]:
    """Palauttaa toteutuneen valuuttakoodin ja alayksikön (esim. SEK -> öre/kWh)."""
    choice = (currency_choice or "AUTO").strip().upper()
    if choice == "AUTO" or choice not in CURRENCY_SUBUNIT_MAP:
        resolved = AREA_DEFAULT_CURRENCY.get(area.upper(), "EUR")
    else:
        resolved = choice
    return resolved, CURRENCY_SUBUNIT_MAP.get(resolved, "c/kWh")


def _build_config_schema(defaults: dict) -> vol.Schema:
    """Rakentaa asennus- ja asetuslomakkeen monimaatuella, valuutoilla ja HA-sensorituella."""
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
    """AI-Sähkövahdin asennusvelho (palvelinvarmennettu lisenssi + monimaa- ja valuuttatuki)."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Mahdollistaa lisenssiavaimen, maan, valuutan ja hintalähteen päivittämisen asetuksista."""
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
                    verified_tier = status["tier"]
                    cleaned["tier"] = verified_tier
                    return self.async_create_entry(
                        title=f"AI-Sähkövahti {cleaned['area']} [{cleaned['currency']}] ({verified_tier.upper()})",
                        data=cleaned,
                    )
                errors["base"] = "invalid_license_key"

        return self.async_show_form(
            step_id="user",
            data_schema=_build_config_schema(user_input or {}),
            errors=errors,
        )


class AISahkovahtiOptionsFlowHandler(config_entries.OptionsFlow):
    """Mahdollistaa lisenssiavaimen, hinta-alueen, valuutan ja oman hintalähteen muokkaamisen."""

    async def async_step_init(self, user_input=None):
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
            step_id="init",
            data_schema=_build_config_schema(user_input or current),
            errors=errors,
        )
