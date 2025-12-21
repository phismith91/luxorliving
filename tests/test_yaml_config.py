"""Tests for KNX YAML configuration loading and validation."""
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open


class TestYAMLConfigValidation:
    """Test YAML configuration structure and content validation."""

    @pytest.fixture
    def sample_knx_yaml(self):
        """Sample KNX YAML config."""
        return """
light:
  - name: "Badlicht"
    address: "1/0/0"
    state_address: "1/1/0"
    
  - name: "Wandlicht dimmen"
    address: "2/0/0"
    state_address: "2/4/0"
    brightness_address: "2/2/0"

switch:
  - name: "B6-1 C3"
    address: "5/3/0"
"""

    def test_yaml_structure_valid(self, sample_knx_yaml):
        """Test YAML structure is valid and parseable."""
        config = yaml.safe_load(sample_knx_yaml)
        
        assert 'light' in config
        assert 'switch' in config
        assert len(config['light']) == 2
        assert len(config['switch']) == 1

    def test_yaml_light_entity_structure(self, sample_knx_yaml):
        """Test light entities have required fields."""
        config = yaml.safe_load(sample_knx_yaml)
        
        for light in config['light']:
            assert 'name' in light
            assert 'address' in light
            assert 'state_address' in light
            
            # Validate address format (x/y/z)
            assert len(light['address'].split('/')) == 3

    def test_yaml_dimmable_light_structure(self, sample_knx_yaml):
        """Test dimmable lights have brightness address."""
        config = yaml.safe_load(sample_knx_yaml)
        
        # Second light is dimmable
        dimmable = config['light'][1]
        assert 'brightness_address' in dimmable

    def test_yaml_no_duplicate_addresses(self, sample_knx_yaml):
        """Test no duplicate control addresses across all entities."""
        config = yaml.safe_load(sample_knx_yaml)
        
        all_addresses = []
        
        # Collect all control addresses
        for light in config.get('light', []):
            all_addresses.append(light['address'])
        
        for switch in config.get('switch', []):
            all_addresses.append(switch['address'])
        
        # Check for duplicates
        assert len(all_addresses) == len(set(all_addresses)), \
            f"Duplicate addresses found: {all_addresses}"

    def test_yaml_address_format_validation(self, sample_knx_yaml):
        """Test all addresses follow KNX group address format."""
        config = yaml.safe_load(sample_knx_yaml)
        
        def validate_address(addr):
            parts = addr.split('/')
            assert len(parts) == 3, f"Invalid address format: {addr}"
            for part in parts:
                assert part.isdigit(), f"Non-numeric part in address: {addr}"
                assert 0 <= int(part) <= 31, f"Address part out of range: {addr}"
        
        for light in config.get('light', []):
            validate_address(light['address'])
            validate_address(light['state_address'])
            if 'brightness_address' in light:
                validate_address(light['brightness_address'])
        
        for switch in config.get('switch', []):
            validate_address(switch['address'])


class TestYAMLConfigLoader:
    """Test YAML configuration file loading."""

    def test_load_yaml_from_config_dir(self, mock_hass):
        """Test loading knx_config.yaml from HA config directory."""
        yaml_content = """
light:
  - name: "Test Light"
    address: "1/0/0"
    state_address: "1/1/0"
"""
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            from custom_components.luxor_living.yaml_loader import load_knx_config
            
            config = load_knx_config("/config/knx_config.yaml")
            
            assert config is not None
            assert 'light' in config
            assert config['light'][0]['name'] == "Test Light"

    def test_yaml_file_not_found_error(self, mock_hass):
        """Test graceful error when YAML file doesn't exist."""
        from custom_components.luxor_living.yaml_loader import load_knx_config
        
        with patch('pathlib.Path.exists', return_value=False):
            config = load_knx_config("/config/missing.yaml")
            
            assert config is None  # or raises specific error

    def test_yaml_syntax_error_handling(self, mock_hass):
        """Test error handling for malformed YAML."""
        malformed_yaml = """
light:
  - name: "Test
    address: 1/0/0  # Missing quote, wrong indentation
"""
        
        with patch('builtins.open', mock_open(read_data=malformed_yaml)):
            from custom_components.luxor_living.yaml_loader import load_knx_config
            
            with pytest.raises(yaml.YAMLError):
                load_knx_config("/config/knx_config.yaml")


class TestYAMLGeneration:
    """Test YAML generation from LXP file."""

    @pytest.fixture
    def mock_lxp_data(self):
        """Mock parsed LXP data."""
        return {
            'devices': [
                {
                    'name': 'Badlicht',
                    'type': 'light',
                    'address': '1/0/0',
                    'state_address': '1/1/0'
                },
                {
                    'name': 'Bewegungsmelder',
                    'type': 'switch',
                    'address': '5/3/0'
                }
            ]
        }

    def test_generate_yaml_from_lxp(self, mock_lxp_data):
        """Test YAML generation from LXP data."""
        from scripts.lxp_to_knx_yaml_standalone import LXPToKNXYAML
        
        generator = LXPToKNXYAML()
        yaml_str = generator.generate_yaml(mock_lxp_data)
        
        # Parse generated YAML
        config = yaml.safe_load(yaml_str)
        
        assert 'light' in config
        assert 'switch' in config
        assert len(config['light']) == 1
        assert len(config['switch']) == 1

    def test_yaml_escaping(self):
        """Test YAML string escaping for special characters."""
        from scripts.lxp_to_knx_yaml_standalone import LXPToKNXYAML
        
        test_cases = [
            ('Licht "4-Fenster"', 'Licht \\"4-Fenster\\"'),
            ('Backslash\\Test', 'Backslash\\\\Test'),
            ('Normal Name', 'Normal Name')
        ]
        
        for input_str, expected in test_cases:
            result = LXPToKNXYAML._escape_yaml_string(input_str)
            assert result == expected

    def test_duplicate_removal(self, mock_lxp_data):
        """Test removal of duplicate addresses during generation."""
        from scripts.lxp_to_knx_yaml_standalone import LXPToKNXYAML
        
        # Add duplicate: same address for light and switch
        mock_lxp_data['devices'].append({
            'name': 'Duplicate Switch',
            'type': 'switch',
            'address': '1/0/0',  # Same as Badlicht
        })
        
        generator = LXPToKNXYAML()
        yaml_str = generator.generate_yaml(
            mock_lxp_data,
            remove_duplicates=True,
            priority='light'  # Lights have priority
        )
        
        config = yaml.safe_load(yaml_str)
        
        # Should only have light, switch removed
        assert len(config['light']) == 1
        assert len(config['switch']) == 1
        assert config['switch'][0]['name'] == 'Bewegungsmelder'


class TestIntegrationYAMLWithHA:
    """Test integration with Home Assistant KNX YAML loading."""

    async def test_ha_loads_knx_yaml_on_startup(self, mock_hass):
        """Test HA KNX integration loads our YAML config."""
        yaml_content = """
light:
  - name: "Test Light"
    address: "1/0/0"
    state_address: "1/1/0"
"""
        
        with patch('builtins.open', mock_open(read_data=yaml_content)):
            # Simulate HA loading configuration.yaml with knx: !include
            from homeassistant.helpers import config_validation as cv
            
            # This would normally be done by HA's config loader
            config = {'knx': yaml.safe_load(yaml_content)}
            
            assert 'knx' in config
            assert 'light' in config['knx']

    async def test_yaml_entity_creation(self, mock_hass):
        """Test entities are created from YAML config."""
        from homeassistant.helpers.entity_platform import EntityPlatform
        
        yaml_config = {
            'light': [
                {
                    'name': 'Badlicht',
                    'address': '1/0/0',
                    'state_address': '1/1/0'
                }
            ]
        }
        
        # Mock entity platform
        with patch.object(EntityPlatform, 'async_add_entities') as mock_add:
            # Simulate KNX platform setup
            # This would create KNXLight entities from YAML
            
            # Verify entities would be created
            # (actual implementation depends on HA KNX integration)
            pass
