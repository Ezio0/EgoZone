# EgoZone Trusted Device Management Guide

## Feature Overview

To balance security and convenience, EgoZone implements a trusted device feature:

1. **Enhanced Security**: Re-enabled password verification, ensuring every access from non-trusted devices requires password verification
2. **Maintained Convenience**: Provides password-free login for trusted devices (such as home computer, work computer, and mobile phone)

## How to Use

### 1. First Login and Trust Device

1. Access EgoZone from your trusted device (such as home computer)
2. Login with the correct administrator password or public access password
3. Check the "Trust this device" option on the login screen
4. The system will record the device information and add it to the trusted list

### 2. View Trusted Devices

You can view the current trusted device list at any time via the API endpoint:
```
GET /api/auth/trusted-devices
```

### 3. Remove Trusted Devices

If a device is no longer trusted, you can remove it via the following API endpoint:
```
DELETE /api/auth/trusted-devices/{device_fingerprint}
```

### 4. Command Line Management Tool

We also provide a command line tool to manage trusted devices:

#### Initialize Trusted Device List
```bash
python manage_trusted_devices.py init
```

#### List All Trusted Devices
```bash
python manage_trusted_devices.py list
```

#### Manually Add Trusted Device
```bash
python manage_trusted_devices.py add --fingerprint <device_fingerprint> --name "<device_name>"
```

#### Remove Trusted Device
```bash
python manage_trusted_devices.py remove --fingerprint <device_fingerprint>
```

## Technical Details

### Device Fingerprint Generation

The system generates unique device fingerprints using the following information:
- User-Agent header
- IP address
- Other request header information

### Data Storage

Trusted device information is stored in the `data/trusted_devices.json` file, containing:
- Device fingerprint
- Device name
- Added time
- Last used time
- User-Agent information

## Security Tips

1. Regularly check the trusted device list and remove unused devices
2. Do not select "Trust this device" on public or shared devices
3. If you suspect a trusted device has been compromised, immediately remove its trusted status
4. Regularly change administrator and access passwords

## API Changes

The following API endpoints have been updated to support trusted device functionality:

### Login Endpoints
- `POST /api/auth/login` - Supports `trust_device` parameter
- `POST /api/auth/access-login` - Supports `trust_device` parameter

### Device Management Endpoints
- `GET /api/auth/trusted-devices` - Get trusted device list
- `DELETE /api/auth/trusted-devices/{device_fingerprint}` - Remove trusted device
- `POST /api/auth/trust-device` - Manually add trusted device