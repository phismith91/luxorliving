"""Tests for knxprod_reader — appId-to-device-name lookup."""

from custom_components.luxor_living.knxprod_reader import (
    APP_ID_TO_DEVICE,
    DEVICE_CATEGORIES,
    get_device_category,
    get_device_name,
)


class TestAppIdToDeviceMap:
    def test_known_switch_devices(self):
        assert APP_ID_TO_DEVICE[18468] == "S4"
        assert APP_ID_TO_DEVICE[18472] == "S8"
        assert APP_ID_TO_DEVICE[18473] == "S16"
        assert APP_ID_TO_DEVICE[18514] == "S1"
        assert APP_ID_TO_DEVICE[18498] == "E1"

    def test_known_dimmer_devices(self):
        assert APP_ID_TO_DEVICE[18546] == "D2"
        assert APP_ID_TO_DEVICE[18548] == "D4"
        assert APP_ID_TO_DEVICE[18544] == "D1"

    def test_known_cover_devices(self):
        assert APP_ID_TO_DEVICE[18516] == "J4"
        assert APP_ID_TO_DEVICE[18520] == "J8"
        assert APP_ID_TO_DEVICE[18517] == "J1"

    def test_known_climate_devices(self):
        assert APP_ID_TO_DEVICE[18502] == "H6"
        assert APP_ID_TO_DEVICE[18497] == "H6 24V"
        assert APP_ID_TO_DEVICE[18518] == "H1"
        assert APP_ID_TO_DEVICE[18577] == "R718"
        assert APP_ID_TO_DEVICE[1042] == "iON2-4"
        assert APP_ID_TO_DEVICE[1048] == "iON8"

    def test_known_binary_input_devices(self):
        assert APP_ID_TO_DEVICE[18486] == "B6"

    def test_known_motion_sensor_devices(self):
        assert APP_ID_TO_DEVICE[18512] == "BI180"
        assert APP_ID_TO_DEVICE[18485] == "BI360"

    def test_known_input_only_devices(self):
        assert APP_ID_TO_DEVICE[18434] == "T2"
        assert APP_ID_TO_DEVICE[18436] == "T4"
        assert APP_ID_TO_DEVICE[18440] == "T8"
        assert APP_ID_TO_DEVICE[1027] == "T2.1"
        assert APP_ID_TO_DEVICE[1029] == "T4.1"
        assert APP_ID_TO_DEVICE[1033] == "T8.1"

    def test_known_unsupported_devices(self):
        assert APP_ID_TO_DEVICE[1170] == "M130"
        assert APP_ID_TO_DEVICE[18585] == "M140"
        assert APP_ID_TO_DEVICE[18482] == "AC IR1"

    def test_map_has_minimum_entries(self):
        assert len(APP_ID_TO_DEVICE) >= 40


class TestGetDeviceName:
    def test_returns_name_for_known_appid(self):
        assert get_device_name(18486) == "B6"
        assert get_device_name(18502) == "H6"
        assert get_device_name(18577) == "R718"

    def test_returns_none_for_unknown_appid(self):
        assert get_device_name(0) is None
        assert get_device_name(9999) is None

    def test_accepts_string_appid(self):
        assert get_device_name("18486") == "B6"
        assert get_device_name("9999") is None

    def test_accepts_empty_string(self):
        assert get_device_name("") is None


class TestDeviceCategories:
    def test_switches_have_switch_category(self):
        assert DEVICE_CATEGORIES["S4"] == "switch"
        assert DEVICE_CATEGORIES["S8"] == "switch"
        assert DEVICE_CATEGORIES["S16"] == "switch"
        assert DEVICE_CATEGORIES["S1"] == "switch"
        assert DEVICE_CATEGORIES["E1"] == "switch"

    def test_dimmers_have_light_category(self):
        assert DEVICE_CATEGORIES["D1"] == "light"
        assert DEVICE_CATEGORIES["D2"] == "light"
        assert DEVICE_CATEGORIES["D4"] == "light"

    def test_covers_have_cover_category(self):
        assert DEVICE_CATEGORIES["J1"] == "cover"
        assert DEVICE_CATEGORIES["J4"] == "cover"
        assert DEVICE_CATEGORIES["J8"] == "cover"

    def test_climate_actuators_have_climate_category(self):
        assert DEVICE_CATEGORIES["H6"] == "climate"
        assert DEVICE_CATEGORIES["H6 24V"] == "climate"
        assert DEVICE_CATEGORIES["H1"] == "climate"

    def test_climate_thermostats_have_climate_category(self):
        assert DEVICE_CATEGORIES["R718"] == "climate"
        assert DEVICE_CATEGORIES["iON2-4"] == "climate"
        assert DEVICE_CATEGORIES["iON8"] == "climate"

    def test_binary_input_has_binary_sensor_category(self):
        assert DEVICE_CATEGORIES["B6"] == "binary_sensor"

    def test_motion_sensors_have_motion_category(self):
        assert DEVICE_CATEGORIES["BI180"] == "motion"
        assert DEVICE_CATEGORIES["BI360"] == "motion"

    def test_t_panels_are_input_only(self):
        assert DEVICE_CATEGORIES["T2"] == "input_only"
        assert DEVICE_CATEGORIES["T4"] == "input_only"
        assert DEVICE_CATEGORIES["T8"] == "input_only"
        assert DEVICE_CATEGORIES["T2.1"] == "input_only"
        assert DEVICE_CATEGORIES["T4.1"] == "input_only"
        assert DEVICE_CATEGORIES["T8.1"] == "input_only"

    def test_unsupported_devices(self):
        assert DEVICE_CATEGORIES["M130"] == "unsupported"
        assert DEVICE_CATEGORIES["M140"] == "unsupported"
        assert DEVICE_CATEGORIES["AC IR1"] == "unsupported"


class TestGetDeviceCategory:
    def test_returns_category_for_known_appid(self):
        assert get_device_category(18486) == "binary_sensor"  # B6
        assert get_device_category(18502) == "climate"  # H6
        assert get_device_category(18436) == "input_only"  # T4
        assert get_device_category(18512) == "motion"  # BI180

    def test_returns_none_for_unknown_appid(self):
        assert get_device_category(9999) is None
        assert get_device_category(0) is None

    def test_accepts_string_appid(self):
        assert get_device_category("18486") == "binary_sensor"
        assert get_device_category("") is None
