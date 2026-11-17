import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import aiohttp

DOMAIN = "aisahkovahti"

class AISahkovahtiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Tarkistetaan lisenssiavain Hetzner-palvelimelta
            valid = await self._verify_license(user_input["license_key"])
            if valid:
                return self.async_create_entry(
                    title=f"AI-Sähkövahti ({user_input['tier'].upper()})",
                    data=user_input
                )
            else:
                errors["base"] = "invalid_license_key"

        schema = vol.Schema({
            vol.Required("license_key"): str,
            vol.Required("tier", default="pro"): vol.In({"pro": "Pro (7 vrk)", "vip": "VIP (30 vrk)"})
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def _verify_license(self, license_key: str) -> bool:
        url = f"https://aisahkovahti.65.109.171.178.sslip.io/api/v1/verify?key={license_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("active", False)
        except Exception:
            pass
        
        # Vaaditaan ehdoton verkkoyhteys ja onnistunut tarkistus (ei päästä läpi ilman palvelimen hyväksyntää)
        return False
