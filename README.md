# GL.iNet KVM Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

This is a custom integration for Home Assistant to monitor and control GL.iNet KVM devices.

**Note:** This project is a fork of [adamoutler/pikvm-homeassistant-integration](https://github.com/adamoutler/pikvm-homeassistant-integration), adapted for GL.iNet KVM devices.   
## Features

- ATX power controls (Power On, Power Off, Reset)
- Monitor power state
- Monitor HDD activity

## Installation

### HACS (Home Assistant Community Store)

1. Ensure that HACS is installed and configured in your Home Assistant setup. If not, follow the instructions [here](https://hacs.xyz/docs/use/).
2. Go to the HACS panel in Home Assistant.
3. Click on the "Integrations" tab.
4. Click on the three dots in the top right corner and select "Custom repositories".
5. Add this repository URL: `https://github.com/Scalegj/glkvm-homeassistant-integration` and select "Integration" as the category.
6. Find "GLiNet KVM" in the list and click "Install".
7. Restart Home Assistant.

### Manual Installation

1. Download the `custom_components` folder from this repository.
2. Copy the `glkvm` folder into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## Configuration

### Adding GLKVM Integration via Home Assistant UI

1. Go to the Home Assistant UI.
2. Navigate to **Configuration** -> **Devices & Services**.
3. Click the **Add Integration** button.
4. Search for "GLiNet KVM".
5. Follow the setup wizard to configure your GLKVM device.

### Configuration Options

- **URL**: The URL or IP address of your GLKVM device.
- **Username**: The username to authenticate with your GLKVM device (default: `admin`).
- **Password**: The password to authenticate with your GLKVM device.

## Usage

Once the GLKVM integration is added and configured, you will have sensors and controls available in Home Assistant:

### Sensors
- **Power State** - Shows if the connected system is on or off
- **HDD Activity** - Shows disk activity status

### Buttons
- **Power On** - Short press power button
- **Power Off** - Short press power button
- **Power Off (Long Press)** - Force power off
- **Reset** - Short press reset button
- **Reset (Long Press)** - Force reset

## Troubleshooting

* Ensure your GLKVM device is accessible from your Home Assistant instance.
* Make sure you have provided the correct URL, username, and password.
* Check the Home Assistant logs for any error messages related to the GLKVM integration.

## Contributing

Contributions are welcome! Please fork this repository and open a pull request with your changes.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
