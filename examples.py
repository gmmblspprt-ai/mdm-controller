"""
Usage Examples for MDM Client
Demonstrates different authentication methods and operations
"""

from mdm_client_advanced import (
    MDMClient, AuthCredentials, AuthMethod, AppConfig, DeviceConfiguration,
    MDMCommandBatch, CommandType
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Example 1: API Key Authentication ====================

def example_api_key_auth():
    """Example using API Key authentication"""
    print("\n" + "="*60)
    print("Example 1: API Key Authentication")
    print("="*60)
    
    credentials = AuthCredentials(
        method=AuthMethod.API_KEY,
        api_key='your-secret-api-key-here',
        verify_ssl=True
    )
    
    client = MDMClient(
        mdm_server_url='https://mdm.example.com',
        credentials=credentials
    )
    
    # Get device list
    devices = client.get_device_list(platform='ios')
    print(f"Found {len(devices)} iOS devices")
    
    for device in devices:
        print(f"  - {device.device_name} ({device.device_id})")
    
    # Lock a device
    if devices:
        device_id = devices[0].device_id
        result = client.lock_device(
            device_id=device_id,
            passcode='123456',
            message='Device locked by MDM'
        )
        print(f"Lock result: {result}")


# ==================== Example 2: OAuth2 Authentication ====================

def example_oauth2_auth():
    """Example using OAuth2 authentication"""
    print("\n" + "="*60)
    print("Example 2: OAuth2 Authentication")
    print("="*60)
    
    credentials = AuthCredentials(
        method=AuthMethod.OAUTH2,
        oauth2_client_id='your-client-id',
        oauth2_client_secret='your-client-secret',
        oauth2_token_url='https://oauth.example.com/token',
        oauth2_scope=['mdm:read', 'mdm:write', 'mdm:admin'],
        verify_ssl=True
    )
    
    client = MDMClient(
        mdm_server_url='https://mdm.example.com',
        credentials=credentials
    )
    
    # Get device information
    device_id = 'device-123'
    try:
        info = client.get_device_information(device_id)
        print(f"Device Info: {info}")
    except Exception as e:
        print(f"Error: {e}")


# ==================== Example 3: SSL/TLS Certificate Authentication ====================

def example_ssl_cert_auth():
    """Example using SSL/TLS certificate authentication"""
    print("\n" + "="*60)
    print("Example 3: SSL/TLS Certificate Authentication")
    print("="*60)
    
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
    
    # Get device list
    devices = client.get_device_list()
    print(f"Total devices: {len(devices)}")


# ==================== Example 4: Hybrid Authentication ====================

def example_hybrid_auth():
    """Example using hybrid authentication (SSL + API Key)"""
    print("\n" + "="*60)
    print("Example 4: Hybrid Authentication (SSL + API Key)")
    print("="*60)
    
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
    
    logger.info("Client configured with hybrid authentication")


# ==================== Example 5: Remote Lock/Unlock ====================

def example_lock_unlock():
    """Example of locking and unlocking devices"""
    print("\n" + "="*60)
    print("Example 5: Remote Lock/Unlock")
    print("="*60)
    
    credentials = AuthCredentials(
        method=AuthMethod.API_KEY,
        api_key='test-api-key',
        verify_ssl=True
    )
    
    client = MDMClient(
        mdm_server_url='https://mdm.example.com',
        credentials=credentials
    )
    
    device_id = 'device-001'
    
    # Lock device
    print(f"\nLocking device {device_id}...")
    lock_result = client.lock_device(
        device_id=device_id,
        passcode='1234',
        message='Device locked for security purposes'
    )
    print(f"Lock result: {lock_result}")
    
    # Unlock device
    print(f"\nUnlocking device {device_id}...")
    unlock_result = client.unlock_device(device_id=device_id)
    print(f"Unlock result: {unlock_result}")


# ==================== Example 6: Wipe Device ====================

def example_wipe_device():
    """Example of wiping a device"""
    print("\n" + "="*60)
    print("Example 6: Wipe Device")
    print("="*60)
    
    credentials = AuthCredentials(
        method=AuthMethod.API_KEY,
        api_key='test-api-key',
        verify_ssl=True
    )
    
    client = MDMClient(
        mdm_server_url='https://mdm.example.com',
        credentials=credentials
    )
    
    device_id = 'device-002'
    
    print(f"\nWiping device {device_id}...")
    wipe_result = client.wipe_device(
        device_id=device_id,
        pin='1234',
        preserve_data=False  # Complete wipe
    )
    print(f"Wipe result: {wipe_result}")


# ==================== Example 7: Install/Remove Applications ====================

def example_app_management():
    """Example of managing applications on devices"""
    print("\n" + "="*60)
    print("Example 7: Install/Remove Applications")
    print("="*60)
    
    credentials = AuthCredentials(
        method=AuthMethod.API_KEY,
        api_key='test-api-key',
        verify_ssl=True
    )
    
    client = MDMClient(
        mdm_server_url='https://mdm.example.com',
        credentials=credentials
    )
    
    device_id = 'device-003'
    
    # Install application
    print(f"\nInstalling application on {device_id}...")
    app_config = AppConfig(
        app_id='com.example.app',
        app_name='Example App',
        app_url='https://example.com/app.ipa',
        version='1.0.0',
        required=True,
        auto_update=True
    )
    
    install_result = client.install_application(device_id, app_config)
    print(f"Install result: {install_result}")
    
    # Remove application
    print(f"\nRemoving application from {device_id}...")
    remove_result = client.remove_application(
        device_id=device_id,
        app_id='com.example.app'
    )
    print(f"Remove result: {remove_result}")
    
    # Update application
    print(f"\nUpdating application on {device_id}...")
    update_result = client.update_application(
        device_id=device_id,
        app_id='com.example.app',
        new_version='2.0.0'
    )
    print(f"Update result: {update_result}")


# ==================== Example 8: Update Device Configurations ====================

def example_device_configurations():
    """Example of updating device configurations"""
    print("\n" + "="*60)
    print("Example 8: Update Device Configurations")
    print("="*60)
    
    credentials = AuthCredentials(
        method=AuthMethod.API_KEY,
        api_key='test-api-key',
        verify_ssl=True
    )
    
    client = MDMClient(
        mdm_server_url='https://mdm.example.com',
        credentials=credentials
    )
    
    device_id = 'device-004'
    
    # Apply security configuration
    print(f"\nApplying security configuration to {device_id}...")
    security_settings = {
        'require_pin': True,
        'pin_length': 6,
        'auto_lock_minutes': 5,
        'disable_camera': False,
        'disable_screenshots': False,
        'enable_firewall': True,
        'require_encryption': True
    }
    
    security_result = client.apply_security_config(device_id, security_settings)
    print(f"Security config result: {security_result}")
    
    # Apply network configuration
    print(f"\nApplying network configuration to {device_id}...")
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
    
    network_result = client.apply_network_config(device_id, network_settings)
    print(f"Network config result: {network_result}")
    
    # Apply device restrictions
    print(f"\nApplying device restrictions to {device_id}...")
    restrictions = {
        'disable_app_store': True,
        'disable_settings': False,
        'disable_camera': False,
        'allowed_apps': [
            'com.example.app1',
            'com.example.app2'
        ],
        'disable_icloud_sync': False
    }
    
    restrictions_result = client.apply_device_restrictions(device_id, restrictions)
    print(f"Restrictions result: {restrictions_result}")


# ==================== Example 9: Device Enrollment ====================

def example_device_enrollment():
    """Example of enrolling and unenrolling devices"""
    print("\n" + "="*60)
    print("Example 9: Device Enrollment")
    print("="*60)
    
    credentials = AuthCredentials(
        method=AuthMethod.API_KEY,
        api_key='test-api-key',
        verify_ssl=True
    )
    
    client = MDMClient(
        mdm_server_url='https://mdm.example.com',
        credentials=credentials
    )
    
    # Enroll device
    print("\nEnrolling new device...")
    enroll_result = client.enroll_device(
        device_id='new-device-001',
        platform='ios',
        enrollment_token='enrollment-token-xyz',
        device_name='John\'s iPhone'
    )
    print(f"Enrollment result: {enroll_result}")
    
    # Unenroll device
    print("\nUnenrolling device...")
    unenroll_result = client.unenroll_device(device_id='new-device-001')
    print(f"Unenrollment result: {unenroll_result}")


# ==================== Example 10: Batch Operations ====================

def example_batch_operations():
    """Example of batch command execution"""
    print("\n" + "="*60)
    print("Example 10: Batch Operations")
    print("="*60)
    
    credentials = AuthCredentials(
        method=AuthMethod.API_KEY,
        api_key='test-api-key',
        verify_ssl=True
    )
    
    client = MDMClient(
        mdm_server_url='https://mdm.example.com',
        credentials=credentials
    )
    
    # Create batch commands
    batch = MDMCommandBatch(client)
    
    batch.add_lock('device-001', '1234') \
         .add_lock('device-002', '5678') \
         .add_install_app('device-003', AppConfig(
            app_id='com.example.app',
            app_name='Example',
            app_url='https://example.com/app.ipa'
         )) \
         .add_remove_app('device-004', 'com.old.app')
    
    print("\nExecuting batch of 4 commands...")
    results = batch.execute()
    
    for i, result in enumerate(results, 1):
        print(f"  Command {i}: {result['status']}")
        if result['status'] == 'error':
            print(f"    Error: {result['error']}")


# ==================== Example 11: Get Device List and Information ====================

def example_get_devices():
    """Example of retrieving device information"""
    print("\n" + "="*60)
    print("Example 11: Get Device List and Information")
    print("="*60)
    
    credentials = AuthCredentials(
        method=AuthMethod.API_KEY,
        api_key='test-api-key',
        verify_ssl=True
    )
    
    client = MDMClient(
        mdm_server_url='https://mdm.example.com',
        credentials=credentials
    )
    
    # Get all devices
    print("\nGetting all devices...")
    all_devices = client.get_device_list()
    print(f"Total devices: {len(all_devices)}")
    
    # Get iOS devices only
    print("\nGetting iOS devices...")
    ios_devices = client.get_device_list(platform='ios')
    print(f"iOS devices: {len(ios_devices)}")
    for device in ios_devices:
        print(f"  - {device.device_name} ({device.device_id})")
        print(f"    Platform: {device.platform}")
        print(f"    Model: {device.model}")
        print(f"    OS Version: {device.os_version}")
        print(f"    Status: {device.status}")
    
    # Get device details
    if all_devices:
        device_id = all_devices[0].device_id
        print(f"\nGetting details for device {device_id}...")
        device_info = client.get_device_information(device_id)
        print(f"Device Info: {device_info}")
        
        # Get security info
        print(f"\nGetting security info for device {device_id}...")
        security_info = client.get_security_info(device_id)
        print(f"Security Info: {security_info}")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("MDM Client - Usage Examples")
    print("="*60)
    
    # Uncomment examples to run:
    # example_api_key_auth()
    # example_oauth2_auth()
    # example_ssl_cert_auth()
    # example_hybrid_auth()
    # example_lock_unlock()
    # example_wipe_device()
    # example_app_management()
    # example_device_configurations()
    # example_device_enrollment()
    # example_batch_operations()
    # example_get_devices()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
