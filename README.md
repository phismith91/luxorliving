# Theben LUXORliving Custom Integration for Home Assistant

This is a custom integration for Home Assistant to control Theben LUXORliving smart home systems. Since the LUXORliving system cannot be integrated via the standard KNX integration, this custom component provides direct IP-based communication with the LUXORliving controller.

## Features

- **UI-based configuration** via config flow (no YAML configuration needed)
- **Async API client** using aiohttp for efficient communication
- **DataUpdateCoordinator** for optimal polling and data management
- **Multiple platform support**: Lights, Switches, and Sensors
- **Proper logging** with debug information
- **Clean separation** between API logic and Home Assistant integration
- **Multi-language support** (English and German)

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/phismith91/luxorliving`
6. Select category: "Integration"
7. Click "Add"
8. Find "Theben LUXORliving" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/luxorliving` folder to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "LUXORliving"
4. Enter the following information:
   - **Host**: IP address or hostname of your LUXORliving controller
   - **Port**: Port number (default: 80)
   - **Update interval**: How often to poll the system in seconds (default: 30)

## Supported Devices

The integration creates entities for:

- **Lights**: On/Off and dimmable lights
- **Switches**: Binary switches
- **Sensors**: Temperature, humidity, illuminance, and other sensors

## API Structure

The integration is built following Home Assistant best practices:

- `api.py`: Async API client with proper error handling
- `coordinator.py`: DataUpdateCoordinator for efficient polling
- `config_flow.py`: UI-based configuration
- `__init__.py`: Integration setup and platform loading
- `light.py`, `switch.py`, `sensor.py`: Platform implementations

## Development Notes

This integration is structured as a placeholder/template. The actual API endpoints and data structures need to be adjusted based on the real LUXORliving API documentation:

- Update API endpoints in `const.py`
- Adjust API methods in `api.py` to match actual API
- Update data parsing in platform files based on actual device data structure

## Logging

To enable debug logging for this integration, add the following to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.luxorliving: debug
```

## Requirements

- Home Assistant 2023.1 or newer
- Python 3.11 or newer
- aiohttp >= 3.8.0

## Support

For issues, feature requests, or questions, please open an issue on [GitHub](https://github.com/phismith91/luxorliving/issues).

## License

This project is provided as-is without any warranty.

## Credits

Developed for integration with Theben LUXORliving smart home systems.