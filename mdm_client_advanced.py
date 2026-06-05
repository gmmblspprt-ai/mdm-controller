"""
Advanced MDM (Mobile Device Management) Client with Authentication
Supports:
- Remote Lock/Unlock
- Device Wipe
- Install/Remove Applications
- Update Configurations
- Multiple Authentication Methods (SSL/TLS, API Key, OAuth2)
"""

import requests
import json
import ssl
import logging
import hmac
import hashlib
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
from urllib.parse import urljoin
import jwt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Authentication Methods"""
    SSL_CERTIFICATE = "ssl_cert"
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    HYBRID = "hybrid"  # Combination of multiple methods


class CommandType(Enum):
    """Supported MDM Command Types"""
    # Device Control
    LOCK_DEVICE = "DeviceLock"
    UNLOCK_DEVICE = "DeviceUnlock"
    WIPE_DEVICE = "EraseDevice"
    RESTART_DEVICE = "RestartDevice"
    SHUTDOWN_DEVICE = "ShutDownDevice"
    
    # Applications
    INSTALL_APPLICATION = "InstallApplication"
    REMOVE_APPLICATION = "RemoveApplication"
    UPDATE_APPLICATION = "UpdateApplication"
    
    # Configuration
    UPDATE_CONFIGURATION = "UpdateConfiguration"
    SECURITY_CONFIG = "SecurityConfiguration"
    NETWORK_CONFIG = "NetworkConfiguration"
    DEVICE_RESTRICTIONS = "DeviceRestrictions"
    
    # Information
    DEVICE_INFORMATION = "DeviceInformation"
    SECURITY_INFO = "SecurityInfo"


@dataclass
class AuthCredentials:
    """Authentication Credentials"""
    method: AuthMethod
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    api_key: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_token_url: Optional[str] = None
    oauth2_scope: Optional[List[str]] = None
    verify_ssl: bool = True


@dataclass
class MDMDevice:
    """MDM Device Information"""
    device_id: str
    device_name: str
    platform: str  # "ios" or "android"
    enrollment_id: Optional[str] = None
    model: Optional[str] = None
    os_version: Optional[str] = None
    serial_number: Optional[str] = None
    last_checkin: Optional[str] = None
    status: Optional[str] = None


@dataclass
class AppConfig:
    """Application Configuration"""
    app_id: str
    app_name: str
    app_url: Optional[str] = None
    version: Optional[str] = None
    required: bool = False
    auto_update: bool = False


@dataclass
class DeviceConfiguration:
    """Device Configuration"""
    config_id: str
    name: str
    config_type: str  # "security", "network", "restrictions"
    settings: Dict[str, Any]
    active: bool = True


class OAuth2Manager:
    """Manage OAuth2 authentication"""
    
    def __init__(self, credentials: AuthCredentials):
        self.credentials = credentials
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.session = requests.Session()
    
    def get_access_token(self) -> str:
        """
        Get OAuth2 access token
        
        Returns:
            Access token
        """
        # Return existing token if still valid
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            logger.info("Using cached OAuth2 token")
            return self.access_token
        
        logger.info("Requesting new OAuth2 token")
        
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.credentials.oauth2_client_id,
            'client_secret': self.credentials.oauth2_client_secret,
        }
        
        if self.credentials.oauth2_scope:
            payload['scope'] = ' '.join(self.credentials.oauth2_scope)
        
        try:
            response = self.session.post(
                self.credentials.oauth2_token_url,
                data=payload,
                timeout=10
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            
            # Set expiry time (subtract 60 seconds for safety)
            expires_in = token_data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
            
            logger.info(f"OAuth2 token obtained, expires in {expires_in} seconds")
            return self.access_token
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get OAuth2 token: {e}")
            raise


class MDMClient:
    """
    Advanced MDM Client with Multiple Authentication Methods
    """
    
    def __init__(
        self,
        mdm_server_url: str,
        credentials: AuthCredentials,
        timeout: int = 30
    ):
        """
        Initialize MDM Client
        
        Args:
            mdm_server_url: Base URL of MDM server
            credentials: Authentication credentials
            timeout: Request timeout in seconds
        """
        self.mdm_server_url = mdm_server_url.rstrip('/')
        self.credentials = credentials
        self.timeout = timeout
        self.session = requests.Session()
        
        # Initialize OAuth2 manager if needed
        self.oauth2_manager: Optional[OAuth2Manager] = None
        if credentials.method in [AuthMethod.OAUTH2, AuthMethod.HYBRID]:
            self.oauth2_manager = OAuth2Manager(credentials)
        
        self._configure_session()
    
    def _configure_session(self) -> None:
        """Configure requests session with appropriate authentication"""
        
        # Configure SSL/TLS
        if self.credentials.method in [AuthMethod.SSL_CERTIFICATE, AuthMethod.HYBRID]:
            if self.credentials.ssl_cert and self.credentials.ssl_key:
                self.session.cert = (
                    self.credentials.ssl_cert,
                    self.credentials.ssl_key
                )
                logger.info("SSL/TLS certificates configured")
        
        # Set SSL verification
        self.session.verify = self.credentials.verify_ssl
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'MDM-Client/2.0',
            'Accept': 'application/json'
        })
        
        # Add API Key if using that method
        if self.credentials.method in [AuthMethod.API_KEY, AuthMethod.HYBRID]:
            if self.credentials.api_key:
                self.session.headers.update({
                    'X-API-Key': self.credentials.api_key,
                    'Authorization': f'Bearer {self.credentials.api_key}'
                })
                logger.info("API Key authentication configured")
    
    def _add_auth_headers(self) -> Dict[str, str]:
        """
        Add authentication headers for current request
        
        Returns:
            Headers dictionary
        """
        headers = {}
        
        if self.credentials.method in [AuthMethod.OAUTH2, AuthMethod.HYBRID]:
            if self.oauth2_manager:
                token = self.oauth2_manager.get_access_token()
                headers['Authorization'] = f'Bearer {token}'
        
        return headers
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to MDM server
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Response JSON
        """
        url = urljoin(self.mdm_server_url, endpoint)
        
        # Add authentication headers
        headers = self._add_auth_headers()
        
        try:
            logger.debug(f"{method} {url}")
            
            if method.upper() == 'GET':
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
            elif method.upper() == 'POST':
                response = self.session.post(
                    url,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
            elif method.upper() == 'PUT':
                response = self.session.put(
                    url,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
            elif method.upper() == 'DELETE':
                response = self.session.delete(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            try:
                return response.json()
            except json.JSONDecodeError:
                return {'status': 'success', 'response_code': response.status_code}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    # ==================== Device Control Commands ====================
    
    def lock_device(
        self,
        device_id: str,
        passcode: Optional[str] = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Remote lock a device
        
        Args:
            device_id: Device identifier
            passcode: Optional passcode to set
            message: Optional lock message
            
        Returns:
            Command response
        """
        params = {}
        if passcode:
            params['passcode'] = passcode
        if message:
            params['message'] = message
        
        logger.info(f"Locking device: {device_id}")
        return self._send_device_command(device_id, CommandType.LOCK_DEVICE, params)
    
    def unlock_device(self, device_id: str, pin: Optional[str] = None) -> Dict[str, Any]:
        """
        Remote unlock a device
        
        Args:
            device_id: Device identifier
            pin: Optional PIN for confirmation
            
        Returns:
            Command response
        """
        params = {}
        if pin:
            params['pin'] = pin
        
        logger.info(f"Unlocking device: {device_id}")
        return self._send_device_command(device_id, CommandType.UNLOCK_DEVICE, params)
    
    def wipe_device(
        self,
        device_id: str,
        pin: Optional[str] = None,
        preserve_data: bool = False
    ) -> Dict[str, Any]:
        """
        Remote wipe a device (erase all data)
        
        Args:
            device_id: Device identifier
            pin: Optional PIN for confirmation
            preserve_data: Whether to preserve some data
            
        Returns:
            Command response
        """
        params = {
            'preserve_data': preserve_data
        }
        if pin:
            params['pin'] = pin
        
        logger.warning(f"Wiping device: {device_id}")
        return self._send_device_command(device_id, CommandType.WIPE_DEVICE, params)
    
    def restart_device(self, device_id: str) -> Dict[str, Any]:
        """Restart a device remotely"""
        logger.info(f"Restarting device: {device_id}")
        return self._send_device_command(device_id, CommandType.RESTART_DEVICE)
    
    # ==================== Application Management ====================
    
    def install_application(
        self,
        device_id: str,
        app_config: AppConfig
    ) -> Dict[str, Any]:
        """
        Install an application on a device
        
        Args:
            device_id: Device identifier
            app_config: Application configuration
            
        Returns:
            Command response
        """
        params = asdict(app_config)
        logger.info(f"Installing app '{app_config.app_name}' on device {device_id}")
        return self._send_device_command(
            device_id,
            CommandType.INSTALL_APPLICATION,
            params
        )
    
    def remove_application(
        self,
        device_id: str,
        app_id: str
    ) -> Dict[str, Any]:
        """
        Remove an application from a device
        
        Args:
            device_id: Device identifier
            app_id: Application identifier
            
        Returns:
            Command response
        """
        params = {'app_id': app_id}
        logger.info(f"Removing app '{app_id}' from device {device_id}")
        return self._send_device_command(
            device_id,
            CommandType.REMOVE_APPLICATION,
            params
        )
    
    def update_application(
        self,
        device_id: str,
        app_id: str,
        new_version: str
    ) -> Dict[str, Any]:
        """
        Update an application on a device
        
        Args:
            device_id: Device identifier
            app_id: Application identifier
            new_version: New version to update to
            
        Returns:
            Command response
        """
        params = {
            'app_id': app_id,
            'new_version': new_version
        }
        logger.info(f"Updating app '{app_id}' to version {new_version} on device {device_id}")
        return self._send_device_command(
            device_id,
            CommandType.UPDATE_APPLICATION,
            params
        )
    
    # ==================== Configuration Management ====================
    
    def update_configuration(
        self,
        device_id: str,
        config: DeviceConfiguration
    ) -> Dict[str, Any]:
        """
        Update device configuration
        
        Args:
            device_id: Device identifier
            config: Device configuration object
            
        Returns:
            Command response
        """
        params = {
            'config_id': config.config_id,
            'name': config.name,
            'config_type': config.config_type,
            'settings': config.settings
        }
        logger.info(f"Updating configuration '{config.name}' on device {device_id}")
        return self._send_device_command(
            device_id,
            CommandType.UPDATE_CONFIGURATION,
            params
        )
    
    def apply_security_config(
        self,
        device_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply security configuration to device
        
        Args:
            device_id: Device identifier
            settings: Security settings dictionary
                - require_pin: bool
                - pin_length: int
                - auto_lock_minutes: int
                - disable_camera: bool
                - disable_screenshots: bool
                - etc.
            
        Returns:
            Command response
        """
        params = {'settings': settings}
        logger.info(f"Applying security configuration to device {device_id}")
        return self._send_device_command(
            device_id,
            CommandType.SECURITY_CONFIG,
            params
        )
    
    def apply_network_config(
        self,
        device_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply network configuration to device
        
        Args:
            device_id: Device identifier
            settings: Network settings dictionary
                - wifi_networks: list
                - vpn_config: dict
                - proxy_settings: dict
                - etc.
            
        Returns:
            Command response
        """
        params = {'settings': settings}
        logger.info(f"Applying network configuration to device {device_id}")
        return self._send_device_command(
            device_id,
            CommandType.NETWORK_CONFIG,
            params
        )
    
    def apply_device_restrictions(
        self,
        device_id: str,
        restrictions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply device restrictions
        
        Args:
            device_id: Device identifier
            restrictions: Restrictions dictionary
                - disable_app_store: bool
                - disable_settings: bool
                - disable_camera: bool
                - allowed_apps: list
                - etc.
            
        Returns:
            Command response
        """
        params = {'restrictions': restrictions}
        logger.info(f"Applying restrictions to device {device_id}")
        return self._send_device_command(
            device_id,
            CommandType.DEVICE_RESTRICTIONS,
            params
        )
    
    # ==================== Device Information ====================
    
    def get_device_information(self, device_id: str) -> Dict[str, Any]:
        """Get detailed device information"""
        logger.info(f"Fetching device information for: {device_id}")
        return self._make_request('GET', f'/api/devices/{device_id}')
    
    def get_device_list(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[MDMDevice]:
        """
        Get list of enrolled devices
        
        Args:
            platform: Filter by platform ('ios' or 'android')
            status: Filter by status ('active', 'inactive', etc.)
            
        Returns:
            List of MDM devices
        """
        params = {}
        if platform:
            params['platform'] = platform
        if status:
            params['status'] = status
        
        logger.info("Fetching device list...")
        response = self._make_request('GET', '/api/devices', params=params)
        
        devices = []
        for device_data in response.get('devices', []):
            devices.append(MDMDevice(
                device_id=device_data['device_id'],
                device_name=device_data.get('device_name', 'Unknown'),
                platform=device_data.get('platform', 'unknown'),
                enrollment_id=device_data.get('enrollment_id'),
                model=device_data.get('model'),
                os_version=device_data.get('os_version'),
                serial_number=device_data.get('serial_number'),
                last_checkin=device_data.get('last_checkin'),
                status=device_data.get('status')
            ))
        
        return devices
    
    def get_security_info(self, device_id: str) -> Dict[str, Any]:
        """Get security information for a device"""
        logger.info(f"Fetching security info for device: {device_id}")
        return self._send_device_command(device_id, CommandType.SECURITY_INFO)
    
    # ==================== Command Management ====================
    
    def _send_device_command(
        self,
        device_id: str,
        command_type: CommandType,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a command to a device via MDM
        
        Args:
            device_id: Device identifier
            command_type: Type of command
            parameters: Command parameters
            
        Returns:
            Command response
        """
        payload = {
            'device_id': device_id,
            'command': command_type.value,
            'timestamp': self._get_timestamp(),
        }
        
        if parameters:
            payload['parameters'] = parameters
        
        return self._make_request('POST', '/api/commands', data=payload)
    
    def get_command_status(self, command_id: str) -> Dict[str, Any]:
        """Get status of a command"""
        logger.info(f"Fetching command status: {command_id}")
        return self._make_request('GET', f'/api/commands/{command_id}')
    
    # ==================== Device Enrollment ====================
    
    def enroll_device(
        self,
        device_id: str,
        platform: str,
        enrollment_token: Optional[str] = None,
        device_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enroll a new device into MDM
        
        Args:
            device_id: Device identifier
            platform: Device platform ('ios' or 'android')
            enrollment_token: Enrollment token from device
            device_name: Optional device name
            
        Returns:
            Enrollment response
        """
        payload = {
            'device_id': device_id,
            'platform': platform,
        }
        if enrollment_token:
            payload['enrollment_token'] = enrollment_token
        if device_name:
            payload['device_name'] = device_name
        
        logger.info(f"Enrolling device: {device_id} ({platform})")
        return self._make_request('POST', '/api/devices/enroll', data=payload)
    
    def unenroll_device(self, device_id: str) -> Dict[str, Any]:
        """Unenroll a device from MDM"""
        logger.warning(f"Unenrolling device: {device_id}")
        return self._make_request('DELETE', f'/api/devices/{device_id}')
    
    @staticmethod
    def _get_timestamp() -> int:
        """Get current timestamp in seconds"""
        return int(time.time())


class MDMCommandBatch:
    """Batch processing for MDM commands"""
    
    def __init__(self, client: MDMClient):
        self.client = client
        self.commands: List[Dict[str, Any]] = []
    
    def add_lock(
        self,
        device_id: str,
        passcode: Optional[str] = None
    ) -> 'MDMCommandBatch':
        """Add lock command to batch"""
        self.commands.append({
            'action': 'lock',
            'device_id': device_id,
            'passcode': passcode
        })
        return self
    
    def add_unlock(self, device_id: str) -> 'MDMCommandBatch':
        """Add unlock command to batch"""
        self.commands.append({
            'action': 'unlock',
            'device_id': device_id
        })
        return self
    
    def add_wipe(self, device_id: str) -> 'MDMCommandBatch':
        """Add wipe command to batch"""
        self.commands.append({
            'action': 'wipe',
            'device_id': device_id
        })
        return self
    
    def add_install_app(
        self,
        device_id: str,
        app_config: AppConfig
    ) -> 'MDMCommandBatch':
        """Add install app command to batch"""
        self.commands.append({
            'action': 'install_app',
            'device_id': device_id,
            'app_config': app_config
        })
        return self
    
    def add_remove_app(
        self,
        device_id: str,
        app_id: str
    ) -> 'MDMCommandBatch':
        """Add remove app command to batch"""
        self.commands.append({
            'action': 'remove_app',
            'device_id': device_id,
            'app_id': app_id
        })
        return self
    
    def execute(self) -> List[Dict[str, Any]]:
        """Execute all commands in batch"""
        results = []
        logger.info(f"Executing batch of {len(self.commands)} commands")
        
        for cmd in self.commands:
            try:
                if cmd['action'] == 'lock':
                    result = self.client.lock_device(
                        cmd['device_id'],
                        cmd.get('passcode')
                    )
                elif cmd['action'] == 'unlock':
                    result = self.client.unlock_device(cmd['device_id'])
                elif cmd['action'] == 'wipe':
                    result = self.client.wipe_device(cmd['device_id'])
                elif cmd['action'] == 'install_app':
                    result = self.client.install_application(
                        cmd['device_id'],
                        cmd['app_config']
                    )
                elif cmd['action'] == 'remove_app':
                    result = self.client.remove_application(
                        cmd['device_id'],
                        cmd['app_id']
                    )
                
                results.append({'status': 'success', 'result': result})
            except Exception as e:
                logger.error(f"Batch command failed: {e}")
                results.append({'status': 'error', 'error': str(e)})
        
        self.commands.clear()
        return results


if __name__ == '__main__':
    print("MDM Client Advanced Module")
