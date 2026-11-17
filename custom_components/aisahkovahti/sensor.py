import logging
import async_timeout
from datetime import timedelta
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(hours=1)

async def async_setup_entry(hass, config_entry, async_add_entities):
    license_key = config_entry.data.get("license_key", "FREE")
    tier = config_entry.data.get("tier", "pro")
    
    coordinator = AISahkovahtiDataCoordinator(hass, license_key, tier)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        AISahkovahtiBestChargingSensor(coordinator),
        AISahkovahtiPriceSpikeSensor(coordinator),
        AISahkovahtiLegionellaStatusSensor(coordinator)
    ])

class AISahkovahtiDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, license_key, tier):
        self.hass = hass
        self.license_key = license_key
        self.tier = tier
        super().__init__(hass, _LOGGER, name="AI-Sähkövahti", update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        url = f"https://aisahkovahti.65.109.171.178.sslip.io/api/v1/forecast?key={self.license_key}&tier={self.tier}"
        session = async_get_clientsession(self.hass)
        
        try:
            async with async_timeout.timeout(15):
                async with session.get(url) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Palvelin vastasi virhekoodilla: {response.status}")
                    
                    data = await response.json()
                    return data
        except Exception as error:
            _LOGGER.warning(f"Yhteysvirhe AI-Sähkövahtiin, käytetään varatietoja: {error}")
            # Varatiedot, jos yhteys palvelimeen katkeaa hetkellisesti
            return {
                "best_hours": ["02:00", "03:00", "04:00"],
                "spike_warning": False,
                "min_water_temp_allowed": 55.0,
                "legionella_status": "Turvallinen (Min. +55°C)"
            }

class AISahkovahtiBestChargingSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "AI-Sähkövahti Optimaaliset Lataustunnit"
        self._attr_unique_id = "aisahkovahti_best_hours"

    @property
    def native_value(self):
        return ", ".join(self.coordinator.data.get("best_hours", []))

    @property
    def extra_state_attributes(self):
        return {"raw_hours": self.coordinator.data.get("best_hours", [])}

class AISahkovahtiPriceSpikeSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "AI-Sähkövahti Hintapiikkivaroitus"
        self._attr_unique_id = "aisahkovahti_spike_warning"

    @property
    def native_value(self):
        return self.coordinator.data.get("spike_warning", False)

class AISahkovahtiLegionellaStatusSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_name = "AI-Sähkövahti Legionella-turvavahti"
        self._attr_unique_id = "aisahkovahti_legionella_status"

    @property
    def native_value(self):
        return self.coordinator.data.get("legionella_status", "Turvallinen (Min. +55°C)")
