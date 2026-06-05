# MDM (Mobile Device Management) Client

Python client library for managing iOS and Android devices through MDM protocols with multiple authentication methods.

## ✨ Features

### 🔐 Device Control
- 🔒 **Remote Lock** - Lock devices remotely with optional passcode
- 🔓 **Remote Unlock** - Unlock devices
- 🗑️ **Wipe Device** - Factory reset and erase all data
- 🔄 **Restart** - Restart device remotely
- 🛑 **Shutdown** - Shutdown device remotely

### 📲 Application Management
- 📦 **Install Apps** - Install applications on devices
- ❌ **Remove Apps** - Remove applications from devices
- ⬆️ **Update Apps** - Update applications to new versions

### ⚙️ Configuration Management
- 🔐 **Security Configuration** - Set PIN requirements, auto-lock, encryption
- 🌐 **Network Configuration** - Configure WiFi, VPN, proxy settings
- 🚫 **Device Restrictions** - Restrict features and allowed applications
- 🎛️ **Custom Configurations** - Apply custom device settings

### 🔑 Authentication Methods
- 🔓 **API Key** - Simple API key authentication
- 🔐 **OAuth2** - OAuth2 bearer token authentication with auto-refresh
- 🛡️ **SSL/TLS Certificates** - Mutual TLS (mTLS) authentication
- 🔗 **Hybrid** - Combination of multiple authentication methods

### 📱 Device Management
- 📝 **Device Enrollment** - Enroll new devices into MDM
- 🚪 **Unenrollment** - Remove devices from MDM
- 📋 **Device List** - Get list of enrolled devices with filters
- ℹ️ **Device Information** - Get detailed device information

### 🚀 Batch Operations
- ⚡ **Batch Processing** - Execute multiple commands efficiently
- 📦 **Command Queue** - Queue and execute commands in sequence

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/gmmblspprt-ai/mdm-controller.git
cd mdm-controller

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### Example 1: Using API Key

```python
from mdm_client_advanced import MDMClient, AuthCredentials, AuthMethod

credentials = AuthCredentials(
    method=AuthMethod.API_KEY,
    api_key='your-api-key',
    verify_ssl=True
)

client = MDMClient(
    mdm_server_url='https://mdm.example.com',
    credentials=credentials
)

# Get devices
devices = client.get_device_list(platform='ios')

# Lock a device
client.lock_device('device-001', passcode='1234')
```

### Example 2: Using OAuth2

```python
credentials = AuthCredentials(
    method=AuthMethod.OAUTH2,
    oauth2_client_id='your-client-id',
    oauth2_client_secret='your-client-secret',
    oauth2_token_url='https://oauth.example.com/token',
    oauth2_scope=['mdm:read', 'mdm:write'],
    verify_ssl=True
)

client = MDMClient(
    mdm_server_url='https://mdm.example.com',
    credentials=credentials
)
```

### Example 3: Using SSL/TLS Certificates

```python
credentials = AuthCredentials(
    method=AuthMethod.SSL_CERTIFICATE,
    ssl_cert='/path/to/client-cert.pem',
    ssl_key='/path/to/client-key.pem',
    verify_ssl=True
)

client = MDMClient(
    mdm_server_url='https://mdm.example.com:8443',
    credentials=credentials
)
```

### Example 4: Using Hybrid Authentication

```python
credentials = AuthCredentials(
    method=AuthMethod.HYBRID,
    ssl_cert='/path/to/client-cert.pem',
    ssl_key='/path/to/client-key.pem',
    api_key='your-api-key',
    verify_ssl=True
)

client = MDMClient(
    mdm_server_url='https://mdm.example.com',
    credentials=credentials
)
```

## 💡 Common Operations

### Remote Lock/Unlock

```python
# Lock device
client.lock_device(
    device_id='device-001',
    passcode='1234',
    message='Device locked for security'
)

# Unlock device
client.unlock_device(device_id='device-001')
```

### Wipe Device

```python
client.wipe_device(
    device_id='device-001',
    pin='1234',
    preserve_data=False  # Complete wipe
)
```

### Install/Remove Applications

```python
from mdm_client_advanced import AppConfig

# Install app
app = AppConfig(
    app_id='com.example.app',
    app_name='Example App',
    app_url='https://example.com/app.ipa',
    version='1.0.0',
    required=True,
    auto_update=True
)
client.install_application('device-001', app)

# Remove app
client.remove_application('device-001', 'com.example.app')

# Update app
client.update_application('device-001', 'com.example.app', '2.0.0')
```

### Security Configuration

```python
security_settings = {
    'require_pin': True,
    'pin_length': 6,
    'auto_lock_minutes': 5,
    'disable_camera': False,
    'disable_screenshots': False,
    'enable_firewall': True,
    'require_encryption': True
}

client.apply_security_config('device-001', security_settings)
```

### Network Configuration

```python
network_settings = {
    'wifi_networks': [
        {
            'ssid': 'Company-WiFi',
            'password': 'secure-password',
            'auto_connect': True
        }
    ],
    'vpn_config': {
        'enabled': True,
        'server': 'vpn.example.com',
        'protocol': 'IKEv2'
    },
    'proxy_settings': {
        'enabled': False
    }
}

client.apply_network_config('device-001', network_settings)
```

### Device Restrictions

```python
restrictions = {
    'disable_app_store': True,
    'disable_settings': False,
    'disable_camera': False,
    'allowed_apps': ['com.app1', 'com.app2'],
    'disable_icloud_sync': False
}

client.apply_device_restrictions('device-001', restrictions)
```

### Batch Operations

```python
from mdm_client_advanced import MDMCommandBatch

batch = MDMCommandBatch(client)

batch.add_lock('device-001', '1234') \
     .add_lock('device-002', '5678') \
     .add_install_app('device-003', app_config) \
     .add_remove_app('device-004', 'com.old.app')

results = batch.execute()
```

### Device Enrollment

```python
# Enroll device
client.enroll_device(
    device_id='new-device',
    platform='ios',
    enrollment_token='token-xyz',
    device_name='John\'s iPhone'
)

# Unenroll device
client.unenroll_device(device_id='new-device-001')
```

### Get Device Information

```python
# Get all devices
devices = client.get_device_list()

# Get iOS devices
ios_devices = client.get_device_list(platform='ios')

# Get device details
info = client.get_device_information('device-001')

# Get security information
security_info = client.get_security_info('device-001')

# Get command status
status = client.get_command_status('command-123')
```

## 🖥️ Supported Platforms

- **iOS** - Apple iPhone, iPad
- **Android** - Android Enterprise devices

## 📊 Authentication Methods Comparison

| Method | Security | Ease of Use | Refresh | Best For |
|--------|----------|-------------|---------|----------|
| API Key | Medium | Easy | Manual | Simple integrations |
| OAuth2 | High | Medium | Auto | Production systems |
| SSL/TLS | Very High | Hard | N/A | High-security environments |
| Hybrid | Very High | Medium | Auto | Enterprise deployments |

## 📚 API Reference

### MDMClient

#### Initialization
```python
MDMClient(mdm_server_url, credentials, timeout=30)
```

#### Device Control Methods
- `lock_device(device_id, passcode=None, message=None)`
- `unlock_device(device_id, pin=None)`
- `wipe_device(device_id, pin=None, preserve_data=False)`
- `restart_device(device_id)`

#### Application Management
- `install_application(device_id, app_config)`
- `remove_application(device_id, app_id)`
- `update_application(device_id, app_id, new_version)`

#### Configuration
- `update_configuration(device_id, config)`
- `apply_security_config(device_id, settings)`
- `apply_network_config(device_id, settings)`
- `apply_device_restrictions(device_id, restrictions)`

#### Device Information
- `get_device_list(platform=None, status=None)`
- `get_device_information(device_id)`
- `get_security_info(device_id)`

#### Enrollment
- `enroll_device(device_id, platform, enrollment_token=None, device_name=None)`
- `unenroll_device(device_id)`

#### Command Management
- `get_command_status(command_id)`

## ⚠️ Error Handling

```python
try:
    client.lock_device('device-001')
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
```

## 📝 Logging

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

## 🔒 Security Best Practices

1. **Never hardcode credentials** - Use environment variables or config files
2. **Use HTTPS** - Always use `verify_ssl=True` in production
3. **Rotate API keys** - Regularly rotate and update API keys
4. **Certificate validation** - Properly validate SSL/TLS certificates
5. **Audit logging** - Log all MDM operations for audit trails
6. **Least privilege** - Use minimal required permissions
7. **Rate limiting** - Implement rate limiting for API calls

## 🌍 Environment Variables

```bash
MDM_SERVER_URL=https://mdm.example.com
MDM_API_KEY=your-api-key
MDM_OAUTH_CLIENT_ID=your-client-id
MDM_OAUTH_CLIENT_SECRET=your-client-secret
MDM_SSL_CERT=/path/to/cert.pem
MDM_SSL_KEY=/path/to/key.pem
```

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guide
- All functions have docstrings
- Error handling is comprehensive
- Tests are included for new features

## 📄 License

MIT License

## 💬 Support

For issues and questions:
1. Check existing issues in the repository
2. Create a new issue with detailed information
3. Contact the development team

## 📋 Changelog

### Version 2.0.0
- Added OAuth2 authentication with auto-refresh
- Added hybrid authentication support
- Added batch command processing
- Added device configuration management
- Improved error handling and logging

### Version 1.0.0
- Initial release
- API key authentication
- Basic device control (lock, wipe, restart)
- Application management
- Device enrollment
