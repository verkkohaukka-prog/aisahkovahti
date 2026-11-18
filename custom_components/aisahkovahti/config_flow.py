import voluptuous as vol
import async_timeout
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "aisahkovahti"


class AISahkovahtiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """AI-Sähkövahdin asennusvelho (palvelinvarmennettu lisenssi ja tilaustaso)."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Mahdollistaa uuden maksetun lisenssiavaimen päivittämisen asetuksista."""
        return AISahkovahtiOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            license_key = user_input["license_key"].strip()

            await self.async_set_unique_id(license_key)
            self._abort_if_unique_id_configured()

            # Palvelin tarkistaa maksun, voimassaolon ja määrittää tilaustason (pro/vip)
            status = await self._verify_license(license_key)
            if status["active"]:
                verified_tier = status["tier"]
                return self.async_create_entry(
                    title=f"AI-Sähkövahti ({verified_tier.upper()})",
                    data={
                        "license_key": license_key,
                        "tier": verified_tier,
                    },
                )
            else:
                errors["base"] = "invalid_license_key"

        schema = vol.Schema(
            {
                vol.Required("license_key"): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

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
                            # Taso luetaan yksinomaan palvelimen vastauksesta
                            server_tier = str(data.get("tier", "pro")).lower()
                            if server_tier not in ("pro", "vip"):
                                server_tier = "pro"
                            return {"active": True, "tier": server_tier}
        except Exception:
            pass

        return {"active": False, "tier": None}


class AISahkovahtiOptionsFlowHandler(config_entries.OptionsFlow):
    """Mahdollistaa uuden lisenssiavaimen syöttämisen tilauksen uusimisen tai päivityksen yhteydessä."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        current_key = self.config_entry.data.get("license_key", "")

        if user_input is not None:
            new_key = user_input["license_key"].strip()
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
                    title=f"AI-Sähkövahti ({verified_tier.upper()})",
                    data={"license_key": new_key, "tier": verified_tier},
                )
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)
                return self.async_create_entry(title="", data={})
            else:
                errors["base"] = "invalid_license_key"

        schema = vol.Schema(
            {
                vol.Required("license_key", default=current_key): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
