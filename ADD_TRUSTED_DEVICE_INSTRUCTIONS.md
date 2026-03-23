# How to Add Devices to Trusted List

## Method 1: Automatic Addition (Recommended)

1. Open a browser on the device you want to trust (such as home computer) and access EgoZone
2. Enter the correct password on the login page
3. **Check the "Trust this device" checkbox** (Important!)
4. Click login
5. The system will automatically record the device information and add it to the trusted list

## Method 2: Manually Get Device Fingerprint and Add

If you want to add a device to the trusted list in advance, you can get the device fingerprint through the following steps:

### Step 1: Get User-Agent String
Open a browser on your home computer, then:

- **Chrome/Firefox/Safari**: Press F12 to open Developer Tools
- In the Console tab, enter the following code and press Enter:
  ```
  navigator.userAgent
  ```

### Step 2: Use Fingerprint Tool to Add Device
1. Run the following command in the EgoZone project directory:
   ```
   python get_device_fingerprint.py
   ```

2. Enter the User-Agent string you just obtained when prompted
3. Enter the device's IP address (if unknown, enter "127.0.0.1" or "unknown")
4. Enter a device name (such as "Home Computer")

### Step 3: Or Get Directly Through Browser
1. Open a browser on the target device and access EgoZone
2. Open Developer Tools (F12)
3. Go to the Console tab
4. Enter the following code to get User-Agent:
   ```
   copy(navigator.userAgent)
   ```
   This will copy the User-Agent to your clipboard

## Verify Trusted Device is Working

### View All Trusted Devices
Use the following command to view trusted devices:
```
python manage_trusted_devices.py list
```

Or access via API:
```
GET /api/auth/trusted-devices
```

### Remove Trusted Device
If a device is no longer trusted, you can delete it:
```
python manage_trusted_devices.py remove --fingerprint <device_fingerprint>
```

## Important Notes

1. **Device Fingerprint is Unique**: Each device's User-Agent and IP combination produces a unique fingerprint
2. **Network Changes Affect**: If your home network IP changes, you may need to re-trust the device
3. **Browser Differences**: Different browsers have different User-Agents and need to be trusted separately
4. **Security**: Only select "Trust this device" for devices you truly control

## Troubleshooting

If a device cannot be correctly identified as a trusted device:

1. Confirm the User-Agent string is consistent
2. Check if a proxy or VPN has changed network identifiers
3. Check if the device fingerprint in server logs matches what's in the trusted list
4. Ensure the data file `data/trusted_devices.json` exists and is properly formatted