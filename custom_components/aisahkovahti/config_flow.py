import voluptuous as vol
import async_timeout
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

DOMAIN = "aisahkovahti"

NORDPOOL_AREAS = [
    {"value": "FI", "label": "FI — Suomi (Finland)"},
    {"value": "SE1", "label": "SE1 — Ruotsi / Luleå (Sweden)"},
    {"value": "SE2", "label": "SE2 — Ruotsi / Sundsvall (Sweden)"},
    {"value": "SE3", "label": "SE3 — Ruotsi / Tukholma (Sweden)"},
    {"value": "SE4", "label": "SE4 — Ruotsi / Malmö (Sweden)"},
    {"value": "NO1", "label": "NO1 — Norja / Oslo (Norway)"},
    {"value": "NO2", "label": "NO2 — Norja / Kristiansand (Norway)"},
    {"value": "NO3", "label": "NO3 — Norja / Trondheim (Norway)"},
    {"value": "NO4", "label": "NO4 — Norja / Tromsø (Norway)"},
    {"value": "NO5", "label": "NO5 — Norja / Bergen (Norway)"},
    {"value": "DK1", "label": "DK1 — Tanska / Länsi (Denmark)"},
    {"value": "DK2", "label": "Tanska / Itä (DK2)"},
    {"value": "EE", "label": "EE — Viro (Estonia)"},
    {"value": "LV", "label": "LV — Latvia"},
    {"value": "LT", "label": "LT — Liettua (Lithuania)"},
    {"value": "GER", "label": "GER / DE — Saksa (Germany)"},
    {"value": "AT", "label": "AT — Itävalta (Austria)"},
    {"value": "NL", "label": "NL — Alankomaat (Netherlands)"},
    {"value": "BE", "label": "BE — Belgia (Belgium)"},
    {"value": "FR", "label": "FR — Ranska (France)"},
    {"value": "PL", "label": "PL — Puola (Poland)"},
    {"value": "UK", "label": "UK — Iso-Britannia (Great Britain)"},
]

PRICE_SOURCE_MODES = [
    {"value": "server", "label": "AI-Sähkövahti API (oletus / FI)"},
    {"value": "ha_entity", "label": "Oma Home Assistant -hintasensori (esim. Nord Pool / ENTSO-E)"},
    {"value": "custom_api", "label": "Oma API-osoite (URL + valinnainen API-avain)"},
]


def _build_config_schema(defaults: dict) -> vol.Schema:
    """Rakentaa asennus- ja asetuslomakkeen monimaatuella."""
    fields = {
        vol.Required("license_key", default=defaults.get("license_key", "")): str,
        vol.Required("area", default=defaults.get("area", "FI")): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=NORDPOOL_AREAS,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(
            "price_source_mode", default=defaults.get("price_source_mode", "server")
        ): selector.SelectSelector(
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
            "custom_price_url",
            default=defaults.get("custom_price_url", ""),
        ): str,
        vol.Optional(
            "custom_api_key",
            default=defaults.get("custom_api_key", ""),
        ): str,
    }
    return vol.Schema(fields)


class AISahkovahtiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """AI-Sähkövahdin asennusvelho (palvelinvarmennettu lisenssi + monimaatuki)."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Mahdollistaa lisenssiavaimen, maan ja hintalähteen päivittämisen asetuksista."""
        return AISahkovahtiOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            license_key = user_input["license_key"].strip()
            area = user_input.get("area", "FI").strip().upper()
            price_source_mode = user_input.get("price_source_mode", "server")
            source_entity_id = (user_input.get("source_entity_id") or "").strip()
            custom_price_url = (user_input.get("custom_price_url") or "").strip()
            custom_api_key = (user_input.get("custom_api_key") or "").strip()

            unique_key = f"{license_key}_{area}"
            await self.async_set_unique_id(unique_key)
            self._abort_if_unique_id_configured()

            if price_source_mode == "ha_entity" and not source_entity_id:
                errors["source_entity_id"] = "missing_source_entity"
            elif price_source_mode == "custom_api" and not custom_price_url:
                errors["custom_price_url"] = "missing_custom_url"
            else:
                status = await self._verify_license(license_key)
                if status["active"]:
                    verified_tier = status["tier"]
                    return self.async_create_entry(
                        title=f"AI-Sähkövahti {area} ({verified_tier.upper()})",
                        data={
                            "license_key": license_key,
                            "tier": verified_tier,
                            "area": area,
                            "price_source_mode": price_source_mode,
                            "source_entity_id": source_entity_id,
                            "custom_price_url": custom_price_url,
                            "custom_api_key": custom_api_key,
                        },
                    )
                else:
                    errors["base"] = "invalid_license_key"

        return self.async_show_form(
            step_id="user",
            data_schema=_build_config_schema(user_input or {}),
            errors=errors,
        )

    async def _verify_license(self, license_key: str) -> dict:
        """Tarkistaa lisenssiavaimen voimassaolon ja maksullisen tason suoraan palvelimelta."""
        url = f"https://aisahkovahti.65.109.171.178.sslip.io/api/v1/verify?key={license_key}"
        session = async_get_clientsession(self.hass)
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


class AISahkovahtiOptionsFlowHandler(config_entries.OptionsFlow):
    """Mahdollistaa lisenssiavaimen, hinta-alueen ja oman hintalähteen muokkaamisen."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        current = dict(self.config_entry.data)

        if user_input is not None:
            new_key = user_input["license_key"].strip()
            area = user_input.get("area", current.get("area", "FI")).strip().upper()
            price_source_mode = user_input.get("price_source_mode", "server")
            source_entity_id = (user_input.get("source_entity_id") or "").strip()
            custom_price_url = (user_input.get("custom_price_url") or "").strip()
            custom_api_key = (user_input.get("custom_api_key") or "").strip()

            if price_source_mode == "ha_entity" and not source_entity_id:
                errors["source_entity_id"] = "missing_source_entity"
            elif price_source_mode == "custom_api" and not custom_price_url:
                errors["custom_price_url"] = "missing_custom_url"
            else:
                url = f"https://aisahkovahti.65.109.171.178.sslip.io/api/v1/verify?key={new_key}"
                session = async_get_clientsession(self.hass)
                is_active = False
                verified_tier = "pro"

                try:
                    async with async_timeout.timeout(10):
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                if data.get("active", False):
                                    is_active = True
                                    server_tier = str(data.get("tier", "pro")).lower()
                                    verified_tier = (
                                        server_tier
                                        if server_tier in ("pro", "vip")
                                        else "pro"
                                    )
                except Exception:
                    pass

                if is_active:
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        title=f"AI-Sähkövahti {area} ({verified_tier.upper()})",
                        data={
                            "license_key": new_key,
                            "tier": verified_tier,
                            "area": area,
                            "price_source_mode": price_source_mode,
                            "source_entity_id": source_entity_id,
                            "custom_price_url": custom_price_url,
                            "custom_api_key": custom_api_key,
                        },
                    )
                    await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                    return self.async_create_entry(title="", data={})
                else:
                    errors["base"] = "invalid_license_key"

        return self.async_show_form(
            step_id="init",
            data_schema=_build_config_schema(user_input or current),
            errors=errors,
        )
