import os
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode
import yaml
import async_timeout
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .config_flow import resolve_currency_and_unit

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=15)


def _load_device_profiles(config_dir: str) -> dict:
    """Lukee käyttäjän /config/device_profiles/ -kansion YAML-tiedostot turvallisesti."""
    profiles_dir = os.path.join(config_dir, "device_profiles")
    result = {
        "cars": [],
        "heat_pumps": [],
        "heating_circuits": [],
        "panels": [],
        "safety": {},
    }

    if not os.path.isdir(profiles_dir):
        return result

    file_map = {
        "cars.yaml": ["cars"],
        "heat_pumps.yaml": ["heat_pumps"],
        "heating_circuits.yaml": ["heating_circuits"],
        "safety.yaml": ["panels", "safety"],
    }

    for filename, keys in file_map.items():
        filepath = os.path.join(profiles_dir, filename)
        if os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f) or {}
                    for key in keys:
                        if key in loaded:
                            result[key] = loaded[key]
            except Exception as err:
                _LOGGER.error(
                    "Virhe luettaessa laiteprofiilitiedostoa %s: %s", filepath, err
                )

    return result


def _parse_dt(val) -> datetime | None:
    """Muuntaa ISO-aikaleiman tai datetime-olion aikavyöhykkeelliseksi datetimeksi."""
    if isinstance(val, datetime):
        return (
            dt_util.as_local(val)
            if val.tzinfo
            else dt_util.as_local(val.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE))
        )
    if isinstance(val, str):
        parsed = dt_util.parse_datetime(val)
        if parsed is not None:
            return dt_util.as_local(parsed)
    return None


def _extract_entries_from_list(
    items, multiplier: float, base_date: datetime | None = None
) -> list[dict]:
    """Muuntaa eri integraatioiden (Nord Pool, ENTSO-E, Tibber, custom JSON) hintalistat yhtenäiseen muotoon."""
    extracted = []
    if not isinstance(items, list):
        return extracted

    for idx, item in enumerate(items):
        start_dt = None
        raw_val = None

        if isinstance(item, dict):
            for time_key in (
                "start",
                "start_time",
                "time",
                "datetime",
                "startsAt",
                "from",
                "timestamp",
            ):
                if time_key in item and item[time_key] is not None:
                    start_dt = _parse_dt(item[time_key])
                    if start_dt:
                        break
            for val_key in ("value", "price", "total", "spot_price", "amount"):
                if val_key in item and item[val_key] is not None:
                    try:
                        raw_val = float(item[val_key])
                        break
                    except (TypeError, ValueError):
                        pass
        elif isinstance(item, (int, float)) and base_date is not None:
            raw_val = float(item)
            start_dt = base_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(hours=idx)

        if start_dt is not None and raw_val is not None:
            extracted.append(
                {
                    "start": start_dt,
                    "hour_label": start_dt.strftime("%H:%M"),
                    "price": round(raw_val * multiplier, 4),
                }
            )

    return extracted


def _parse_ha_entity_prices(
    state_obj, price_attribute: str, multiplier: float
) -> tuple[float | None, list[dict]]:
    """Lukee hinnat käyttäjän omasta Home Assistant -sensorista (Nord Pool / ENTSO-E / Tibber / mukautettu)."""
    if state_obj is None:
        return None, []

    attrs = state_obj.attributes or {}
    now_local = dt_util.now()
    today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_start = today_start + timedelta(days=1)

    current_price = None
    try:
        current_price = round(float(state_obj.state) * multiplier, 4)
    except (TypeError, ValueError):
        current_price = None

    entries: list[dict] = []
    attr_mode = (price_attribute or "auto").strip()

    if attr_mode.lower() != "auto":
        custom_list = attrs.get(attr_mode)
        entries.extend(_extract_entries_from_list(custom_list, multiplier, today_start))
    else:
        # 1. Nord Pool (HACS): raw_today + raw_tomorrow (tai today + tomorrow)
        if "raw_today" in attrs:
            entries.extend(
                _extract_entries_from_list(attrs.get("raw_today"), multiplier, today_start)
            )
            entries.extend(
                _extract_entries_from_list(
                    attrs.get("raw_tomorrow"), multiplier, tomorrow_start
                )
            )
        # 2. ENTSO-E (HACS): prices / prices_today + prices_tomorrow
        elif "prices_today" in attrs or "prices_tomorrow" in attrs:
            entries.extend(
                _extract_entries_from_list(
                    attrs.get("prices_today"), multiplier, today_start
                )
            )
            entries.extend(
                _extract_entries_from_list(
                    attrs.get("prices_tomorrow"), multiplier, tomorrow_start
                )
            )
        elif "prices" in attrs:
            entries.extend(
                _extract_entries_from_list(attrs.get("prices"), multiplier, today_start)
            )
        # 3. Tibber / Octopus / muut: today + tomorrow / data / hourly_prices
        elif "today" in attrs:
            entries.extend(
                _extract_entries_from_list(attrs.get("today"), multiplier, today_start)
            )
            entries.extend(
                _extract_entries_from_list(
                    attrs.get("tomorrow"), multiplier, tomorrow_start
                )
            )
        else:
            for fallback_key in ("hourly_prices", "data", "forecast", "intervals"):
                if fallback_key in attrs:
                    entries.extend(
                        _extract_entries_from_list(
                            attrs.get(fallback_key), multiplier, today_start
                        )
                    )
                    break

    # Järjestetään ja poistetaan duplikaatit aikaleiman mukaan
    dedup = {}
    for entry in entries:
        dedup[entry["start"].isoformat()] = entry
    sorted_entries = sorted(dedup.values(), key=lambda x: x["start"])

    if current_price is None and sorted_entries:
        for entry in sorted_entries:
            if entry["start"] <= now_local < entry["start"] + timedelta(hours=1):
                current_price = entry["price"]
                break

    return current_price, sorted_entries


def _analyze_local_price_series(
    current_price: float | None,
    entries: list[dict],
    area: str,
    currency: str,
    price_unit: str,
    profiles: dict,
    source_label: str,
) -> dict:
    """Laskee halvimmat tunnit, hintapiikit ja keskiarvot paikallisesta hintasarjasta."""
    now_local = dt_util.now()
    horizon_end = now_local + timedelta(hours=24)

    upcoming = [
        e
        for e in entries
        if (now_local - timedelta(minutes=59)) <= e["start"] <= horizon_end
    ]
    if not upcoming:
        upcoming = entries

    if upcoming:
        prices = [e["price"] for e in upcoming]
        avg_price = round(sum(prices) / len(prices), 3)
        min_price = round(min(prices), 3)
        max_price = round(max(prices), 3)

        # Valitaan 3 halvinta tuntia kronologiseen järjestykseen
        cheapest_3 = sorted(upcoming, key=lambda x: x["price"])[:3]
        cheapest_3_chrono = sorted(cheapest_3, key=lambda x: x["start"])
        best_hours = [e["hour_label"] for e in cheapest_3_chrono]

        active_price = (
            current_price if current_price is not None else upcoming[0]["price"]
        )
        # Hintapiikki: hinta on yli 1.6x keskihinnan ja selvästi yli nollatason
        spike_warning = bool(
            avg_price > 0
            and active_price >= avg_price * 1.6
            and (active_price - avg_price) > 2.0
        )
    else:
        active_price = current_price
        avg_price = current_price
        min_price = current_price
        max_price = current_price
        best_hours = ["02:00", "03:00", "04:00"]
        spike_warning = False

    return {
        "area": area,
        "currency": currency,
        "price_unit": price_unit,
        "price_source": source_label,
        "current_price": active_price,
        "average_price": avg_price,
        "min_price": min_price,
        "max_price": max_price,
        "best_hours": best_hours,
        "spike_warning": spike_warning,
        "min_water_temp_allowed": 55.0,
        "legionella_status": "Turvallinen (Min. +55°C)",
        "hourly_prices": [
            {
                "start": e["start"].isoformat(),
                "hour": e["hour_label"],
                "price": e["price"],
            }
            for e in upcoming[:48]
        ],
        "device_profiles": profiles,
    }


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = AISahkovahtiDataCoordinator(hass, config_entry.data)
    await coordinator.async_config_entry_first_refresh()

    async def handle_reload_profiles(call):
        """Mahdollistaa laiteprofiilien uudelleenlatauksen ilman HA:n uudelleenkäynnistystä."""
        await coordinator.async_request_refresh()

    if not hass.services.has_service("aisahkovahti", "reload_profiles"):
        hass.services.async_register(
            "aisahkovahti", "reload_profiles", handle_reload_profiles
        )

    async_add_entities(
        [
            AISahkovahtiCurrentPriceSensor(coordinator, config_entry.entry_id),
            AISahkovahtiBestChargingSensor(coordinator, config_entry.entry_id),
            AISahkovahtiPriceSpikeSensor(coordinator, config_entry.entry_id),
            AISahkovahtiLegionellaStatusSensor(coordinator, config_entry.entry_id),
            AISahkovahtiDeviceProfilesSensor(coordinator, config_entry.entry_id),
        ]
    )


class AISahkovahtiDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_data: dict):
        self.hass = hass
        self.config_data = dict(config_data)
        self.license_key = self.config_data.get("license_key", "FREE")
        self.tier = self.config_data.get("tier", "pro")
        self.area = self.config_data.get("area", "FI").upper()
        currency_choice = self.config_data.get("currency_choice", "AUTO")
        resolved_currency, resolved_unit = resolve_currency_and_unit(
            self.area, currency_choice
        )
        self.currency = self.config_data.get("currency", resolved_currency)
        self.price_unit = self.config_data.get("price_unit", resolved_unit)
        self.price_source_mode = self.config_data.get(
            "price_source_mode",
            "server" if self.area == "FI" else "ha_entity",
        )
        self.source_entity_id = self.config_data.get("source_entity_id", "")
        self.price_attribute = self.config_data.get("price_attribute", "auto")
        self.price_multiplier = float(self.config_data.get("price_multiplier", 1.0))
        self.custom_price_url = self.config_data.get("custom_price_url", "")
        self.custom_api_key = self.config_data.get("custom_api_key", "")

        super().__init__(
            hass,
            _LOGGER,
            name=f"AI-Sähkövahti ({self.area})",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        profiles = await self.hass.async_add_executor_job(
            _load_device_profiles, self.hass.config.config_dir
        )

        # 1. Paikallinen Home Assistant -hintasensori (Nord Pool / ENTSO-E / Tibber jne.)
        if self.price_source_mode == "ha_entity" and self.source_entity_id:
            state_obj = self.hass.states.get(self.source_entity_id)
            current_price, entries = _parse_ha_entity_prices(
                state_obj, self.price_attribute, self.price_multiplier
            )
            if current_price is not None or entries:
                return _analyze_local_price_series(
                    current_price=current_price,
                    entries=entries,
                    area=self.area,
                    currency=self.currency,
                    price_unit=self.price_unit,
                    profiles=profiles,
                    source_label=f"ha_entity:{self.source_entity_id}",
                )
            _LOGGER.warning(
                "Paikallinen hintasensori %s ei ole vielä valmis tai hintoja ei löytynyt",
                self.source_entity_id,
            )

        # 2. Käyttäjän oma API-osoite (tukee {area}- ja {currency}-paikkamerkkejä)
        if self.price_source_mode == "custom_api" and self.custom_price_url:
            custom_url = self.custom_price_url.replace("{area}", self.area).replace(
                "{currency}", self.currency
            )
            headers = {"Accept": "application/json"}
            if self.custom_api_key:
                headers["Authorization"] = f"Bearer {self.custom_api_key}"
                headers["x-api-key"] = self.custom_api_key

            session = async_get_clientsession(self.hass)
            try:
                async with async_timeout.timeout(15):
                    async with session.get(custom_url, headers=headers) as response:
                        if response.status != 200:
                            raise UpdateFailed(
                                f"Oma API vastasi virhekoodilla: {response.status}"
                            )
                        payload = await response.json()
                        raw_list = (
                            payload
                            if isinstance(payload, list)
                            else payload.get("prices")
                            or payload.get("data")
                            or payload.get("hourly_prices")
                            or []
                        )
                        entries = _extract_entries_from_list(
                            raw_list, self.price_multiplier, dt_util.now()
                        )
                        return _analyze_local_price_series(
                            current_price=None,
                            entries=entries,
                            area=self.area,
                            currency=self.currency,
                            price_unit=self.price_unit,
                            profiles=profiles,
                            source_label="custom_api",
                        )
            except Exception as err:
                _LOGGER.warning("Oman API-osoitteen haku epäonnistui: %s", err)

        # 3. AI-Sähkövahti palvelinrajapinta (oletus FI)
        query = urlencode(
            {
                "key": str(self.license_key),
                "tier": str(self.tier),
                "area": str(self.area),
                "currency": str(self.currency),
            }
        )
        url = f"https://aisahkovahti.65.109.171.178.sslip.io/api/v1/forecast?{query}"
        session = async_get_clientsession(self.hass)

        try:
            async with async_timeout.timeout(15):
                async with session.get(url) as response:
                    if response.status in (401, 403):
                        _LOGGER.warning(
                            "Lisenssitarkistus estetty tai vanhentunut (HTTP %s) alueelle %s",
                            response.status,
                            self.area,
                        )
                    if response.status != 200:
                        raise UpdateFailed(
                            f"Palvelin vastasi virhekoodilla: {response.status}"
                        )

                    data = await response.json()
                    data.setdefault("area", self.area)
                    data.setdefault("currency", self.currency)
                    data.setdefault("price_unit", self.price_unit)
                    data.setdefault("price_source", "server")
                    data["device_profiles"] = profiles
                    return data
        except Exception as error:
            _LOGGER.warning(
                "Yhteysvirhe AI-Sähkövahtiin (%s), käytetään varatietoja: %s",
                self.area,
                error,
            )
            return {
                "area": self.area,
                "currency": self.currency,
                "price_unit": self.price_unit,
                "price_source": "fallback",
                "current_price": None,
                "best_hours": ["02:00", "03:00", "04:00"],
                "spike_warning": False,
                "min_water_temp_allowed": 55.0,
                "legionella_status": "Turvallinen (Min. +55°C)",
                "device_profiles": profiles,
            }


class AISahkovahtiCurrentPriceSensor(CoordinatorEntity, SensorEntity):
    """Näyttää valitun alueen nykyisen sähkön hinnan maan omassa valuuttayksikössä."""

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = f"AI-Sähkövahti Sähkön Hinta ({coordinator.area})"
        self._attr_unique_id = f"aisahkovahti_{entry_id}_current_price"
        self._attr_icon = "mdi:cash-multiple"
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_unit_of_measurement(self):
        return self.coordinator.data.get("price_unit", self.coordinator.price_unit)

    @property
    def native_value(self):
        return self.coordinator.data.get("current_price")

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data
        return {
            "area": d.get("area", self.coordinator.area),
            "currency": d.get("currency", self.coordinator.currency),
            "price_unit": d.get("price_unit", self.coordinator.price_unit),
            "price_source": d.get("price_source"),
            "average_price": d.get("average_price"),
            "min_price": d.get("min_price"),
            "max_price": d.get("max_price"),
            "hourly_prices": d.get("hourly_prices", []),
        }


class AISahkovahtiBestChargingSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = (
            f"AI-Sähkövahti Optimaaliset Lataustunnit ({coordinator.area})"
        )
        self._attr_unique_id = f"aisahkovahti_{entry_id}_best_hours"
        self._attr_icon = "mdi:clock-check-outline"

    @property
    def native_value(self):
        return ", ".join(self.coordinator.data.get("best_hours", []))

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data
        return {
            "area": d.get("area", self.coordinator.area),
            "currency": d.get("currency", self.coordinator.currency),
            "raw_hours": d.get("best_hours", []),
        }


class AISahkovahtiPriceSpikeSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = f"AI-Sähkövahti Hintapiikkivaroitus ({coordinator.area})"
        self._attr_unique_id = f"aisahkovahti_{entry_id}_spike_warning"
        self._attr_icon = "mdi:flash-alert"

    @property
    def native_value(self):
        return self.coordinator.data.get("spike_warning", False)


class AISahkovahtiLegionellaStatusSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = f"AI-Sähkövahti Legionella-turvavahti ({coordinator.area})"
        self._attr_unique_id = f"aisahkovahti_{entry_id}_legionella_status"
        self._attr_icon = "mdi:water-thermometer"

    @property
    def native_value(self):
        return self.coordinator.data.get(
            "legionella_status", "Turvallinen (Min. +55°C)"
        )


class AISahkovahtiDeviceProfilesSensor(CoordinatorEntity, SensorEntity):
    """Altistaa käyttäjän laiteprofiilit, ryhmäkeskukset ja turvarajat Home Assistantille."""

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._attr_name = (
            f"AI-Sähkövahti Laitteistoprofiilit & Turvarajat ({coordinator.area})"
        )
        self._attr_unique_id = f"aisahkovahti_{entry_id}_device_profiles"
        self._attr_icon = "mdi:home-lightning-bolt"

    @property
    def native_value(self):
        profiles = self.coordinator.data.get("device_profiles", {})
        cars_count = len(profiles.get("cars", []))
        hp_count = len(profiles.get("heat_pumps", []))
        circuits_count = len(profiles.get("heating_circuits", []))
        panels_count = len(profiles.get("panels", []))
        return f"Autot: {cars_count}, Pumput: {hp_count}, Piirit: {circuits_count}, Keskukset: {panels_count}"

    @property
    def extra_state_attributes(self):
        profiles = self.coordinator.data.get("device_profiles", {})
        return {
            "area": self.coordinator.data.get("area", self.coordinator.area),
            "currency": self.coordinator.data.get("currency", self.coordinator.currency),
            "cars": profiles.get("cars", []),
            "heat_pumps": profiles.get("heat_pumps", []),
            "heating_circuits": profiles.get("heating_circuits", []),
            "panels": profiles.get("panels", []),
            "safety": profiles.get("safety", {}),
        }
