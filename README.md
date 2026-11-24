# GL.iNet KVM for Home Assistant

![GitHub Release](https://img.shields.io/github/v/release/scalegj/glkvm-homeassistant-integration?include_prereleases&display_name=release)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Scalegj/glkvm-homeassistant-integration/tests.yml?label=tests)
![GitHub License](https://img.shields.io/github/license/Scalegj/glkvm-homeassistant-integration)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)

A Home Assistant integration to control GL.iNet KVMs

## Entities

| Entity | Type | Description |
|---|---|---|
| Power | Switch | Presses ATX power button |
| Force Off | Button | Holds ATX power button |
| Reset | Button | Presses ATX reset button |
| Virtual Media | Select | Mounts the selected ISO from KVM storage |
| EDID | Select | Switches to the selected EDID preset |
| Mouse Jiggler | Switch | Toggles the KVM's mouse jiggler |
| USB Connected | Binary Sensor | Status of the KVM's USB (HID) connection |

> [!NOTE]
> Power, Force Off, and Reset requires the GL.iNet ATX Power Control Board

## Installation

### Marketplace

[![Open in Marketplace](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=Scalegj&repository=glkvm-homeassistant-integration&category=integration)

Or in HACS add `https://github.com/Scalegj/glkvm-homeassistant-integration` as a custom repository with type Integration.

### Manual Installation

1. Download the `custom_components` folder from the [latest release](https://github.com/Scalegj/glkvm-homeassistant-integration/releases).
2. Copy the `glkvm` folder into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## Configuration

### Adding GLKVM Integration via Home Assistant UI

1. Navigate to **Settings** -> **Devices & Services**.
2. Click the **Add Integration** button and search for **GL.iNet KVM**.
3. Follow the setup wizard to configure your KVM.

> If upgrading from v0.1.0-alpha/v1.0.0 delete the old entry, restart, and add it again.

### Configuration Options

- **URL**: The URL or IP address of your KVM.
- **Username**: The username to authenticate with your KVM (default: `admin`).
- **Password**: The password to authenticate with your KVM.
- **TOTP Secret**: The 2FA generation secret, not a 6-digit code (Optional, only if 2FA is enabled on the KVM)

## Security Notes

**Certificate verification:** GL.iNet KVMs use a self-signed HTTPS certificate by default, so this integration connects with certificate verification turned off. This can make you susceptible to a man-in-the-middle attack on an insecure network. It is recommended to install a trusted certificate on the KVM and enabled **Verify SSL certificate** in the setup page.

**2FA secret:** To log in automatically with 2FA enabled, Home Assistant has to store your 2FA secret in **plaintext**, meaning anyone with access to home assistant, or it's filesystem, could generate 2FA codes and gain full access to your KVM.

## License

MIT, see [LICENSE](LICENSE.md). 

This project isn't affiliated with GL.iNet.