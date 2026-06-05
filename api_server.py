"""
MDM API Server using FastAPI
Provides RESTful API for MDM Client operations
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from enum import Enum

from mdm_client_advanced import (
    MDMClient, AuthCredentials, AuthMethod, AppConfig,
    DeviceConfiguration, MDMCommandBatch
)
from database import (
    MongoDB, Device, Command, Configuration,
    DeviceStatus, CommandStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="MDM Controller API",
    description="Mobile Device Management REST API",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database
db = MongoDB()

# MDM Client
mdm_client: Optional[MDMClient] = None


# ==================== Pydantic Models ====================

class AuthMethodEnum(str, Enum):
    """Authentication method enum"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SSL_CERTIFICATE = "ssl_cert"
    HYBRID = "hybrid"


class AuthConfig(BaseModel):
    """Authentication configuration"""
    method: AuthMethodEnum
    mdm_server_url: str
    api_key: Optional[str] = None
    oauth2_client_id: Optional[str] = None
    oauth2_client_secret: Optional[str] = None
    oauth2_token_url: Optional[str] = None
    oauth2_scope: Optional[List[str]] = None
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    verify_ssl: bool = True


class DeviceResponse(BaseModel):
    """Device response model"""
    device_id: str
    device_name: str
    platform: str
    model: Optional[str] = None
    os_version: Optional[str] = None
    status: str
    last_checkin: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class CommandRequest(BaseModel):
    """Command request model"""
    device_id: str
    command_type: str
    parameters: Optional[Dict[str, Any]] = None


class CommandResponse(BaseModel):
    """Command response model"""
    command_id: str
    device_id: str
    command_type: str
    status: str
    result: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class LockDeviceRequest(BaseModel):
    """Lock device request"""
    device_id: str
    passcode: Optional[str] = None
    message: Optional[str] = None


class WipeDeviceRequest(BaseModel):
    """Wipe device request"""
    device_id: str
    pin: Optional[str] = None
    preserve_data: bool = False


class InstallAppRequest(BaseModel):
    """Install app request"""
    device_id: str
    app_id: str
    app_name: str
    app_url: Optional[str] = None
    version: Optional[str] = None
    required: bool = False
    auto_update: bool = False


class SecurityConfigRequest(BaseModel):
    """Security configuration request"""
    device_id: str
    settings: Dict[str, Any]


class BatchCommandRequest(BaseModel):
    """Batch command request"""
    commands: List[CommandRequest]


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup():
    """Initialize connections on startup"""
    global mdm_client
    
    logger.info("Starting MDM API Server...")
    
    try:
        # Connect to database
        await db.connect()
        logger.info("Database connected")
        
        # Initialize MDM client with default config
        # In production, this should come from config file or environment
        credentials = AuthCredentials(
            method=AuthMethod.API_KEY,
            api_key="default-key",
            verify_ssl=True
        )
        mdm_client = MDMClient(
            mdm_server_url="https://mdm.example.com",
            credentials=credentials
        )
        logger.info("MDM Client initialized")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise


@app.on_event("shutdown")
async def shutdown():
    """Clean up on shutdown"""
    logger.info("Shutting down MDM API Server...")
    await db.disconnect()


# ==================== Health & Info Endpoints ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/info")
async def info():
    """API information"""
    return {
        "name": "MDM Controller API",
        "version": "2.0.0",
        "description": "Mobile Device Management REST API"
    }


# ==================== Authentication Endpoints ====================

@app.post("/auth/configure")
async def configure_auth(config: AuthConfig):
    """Configure authentication"""
    global mdm_client
    
    try:
        auth_method = AuthMethod[config.method.upper()]
        
        credentials = AuthCredentials(
            method=auth_method,
            api_key=config.api_key,
            oauth2_client_id=config.oauth2_client_id,
            oauth2_client_secret=config.oauth2_client_secret,
            oauth2_token_url=config.oauth2_token_url,
            oauth2_scope=config.oauth2_scope,
            ssl_cert=config.ssl_cert,
            ssl_key=config.ssl_key,
            verify_ssl=config.verify_ssl
        )
        
        mdm_client = MDMClient(
            mdm_server_url=config.mdm_server_url,
            credentials=credentials
        )
        
        logger.info(f"Auth configured: {config.method}")
        return {"status": "configured", "method": config.method}
    
    except Exception as e:
        logger.error(f"Auth configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Device Endpoints ====================

@app.get("/api/devices", response_model=List[DeviceResponse])
async def get_devices(platform: Optional[str] = None, status: Optional[str] = None):
    """Get list of devices"""
    try:
        devices = await db.get_devices(platform=platform, status=status)
        return devices
    except Exception as e:
        logger.error(f"Get devices error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/devices/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str):
    """Get device details"""
    try:
        device = await db.get_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        return device
    except Exception as e:
        logger.error(f"Get device error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/devices/enroll")
async def enroll_device(
    device_id: str,
    platform: str,
    device_name: Optional[str] = None
):
    """Enroll new device"""
    try:
        device = Device(
            device_id=device_id,
            device_name=device_name or device_id,
            platform=platform,
            status=DeviceStatus.ENROLLED.value,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await db.save_device(device)
        logger.info(f"Device enrolled: {device_id}")
        
        return {"status": "enrolled", "device_id": device_id}
    except Exception as e:
        logger.error(f"Enroll device error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/devices/{device_id}")
async def unenroll_device(device_id: str):
    """Unenroll device"""
    try:
        await db.delete_device(device_id)
        logger.warning(f"Device unenrolled: {device_id}")
        return {"status": "unenrolled", "device_id": device_id}
    except Exception as e:
        logger.error(f"Unenroll device error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Command Endpoints ====================

@app.post("/api/commands", response_model=CommandResponse)
async def send_command(request: CommandRequest, background_tasks: BackgroundTasks):
    """Send command to device"""
    try:
        if not mdm_client:
            raise HTTPException(status_code=400, detail="MDM Client not configured")
        
        # Save command to database
        command = Command(
            device_id=request.device_id,
            command_type=request.command_type,
            status=CommandStatus.PENDING.value,
            parameters=request.parameters,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await db.save_command(command)
        
        # Execute command in background
        background_tasks.add_task(
            execute_mdm_command,
            command.command_id,
            request.device_id,
            request.command_type,
            request.parameters
        )
        
        logger.info(f"Command sent: {command.command_id}")
        return command
    
    except Exception as e:
        logger.error(f"Send command error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/commands/{command_id}", response_model=CommandResponse)
async def get_command_status(command_id: str):
    """Get command status"""
    try:
        command = await db.get_command(command_id)
        if not command:
            raise HTTPException(status_code=404, detail="Command not found")
        return command
    except Exception as e:
        logger.error(f"Get command status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Device Control Endpoints ====================

@app.post("/api/devices/{device_id}/lock")
async def lock_device(
    device_id: str,
    request: LockDeviceRequest,
    background_tasks: BackgroundTasks
):
    """Lock device"""
    try:
        if not mdm_client:
            raise HTTPException(status_code=400, detail="MDM Client not configured")
        
        # Create and save command
        command = Command(
            device_id=device_id,
            command_type="DeviceLock",
            status=CommandStatus.PENDING.value,
            parameters={
                "passcode": request.passcode,
                "message": request.message
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await db.save_command(command)
        
        # Execute in background
        background_tasks.add_task(
            mdm_client.lock_device,
            device_id,
            request.passcode,
            request.message
        )
        
        return {"status": "lock_sent", "device_id": device_id}
    except Exception as e:
        logger.error(f"Lock device error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/devices/{device_id}/unlock")
async def unlock_device(device_id: str, background_tasks: BackgroundTasks):
    """Unlock device"""
    try:
        if not mdm_client:
            raise HTTPException(status_code=400, detail="MDM Client not configured")
        
        command = Command(
            device_id=device_id,
            command_type="DeviceUnlock",
            status=CommandStatus.PENDING.value,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await db.save_command(command)
        background_tasks.add_task(mdm_client.unlock_device, device_id)
        
        return {"status": "unlock_sent", "device_id": device_id}
    except Exception as e:
        logger.error(f"Unlock device error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/devices/{device_id}/wipe")
async def wipe_device(
    device_id: str,
    request: WipeDeviceRequest,
    background_tasks: BackgroundTasks
):
    """Wipe device"""
    try:
        if not mdm_client:
            raise HTTPException(status_code=400, detail="MDM Client not configured")
        
        command = Command(
            device_id=device_id,
            command_type="EraseDevice",
            status=CommandStatus.PENDING.value,
            parameters={
                "pin": request.pin,
                "preserve_data": request.preserve_data
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await db.save_command(command)
        background_tasks.add_task(
            mdm_client.wipe_device,
            device_id,
            request.pin,
            request.preserve_data
        )
        
        return {"status": "wipe_sent", "device_id": device_id}
    except Exception as e:
        logger.error(f"Wipe device error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/devices/{device_id}/restart")
async def restart_device(device_id: str, background_tasks: BackgroundTasks):
    """Restart device"""
    try:
        if not mdm_client:
            raise HTTPException(status_code=400, detail="MDM Client not configured")
        
        command = Command(
            device_id=device_id,
            command_type="RestartDevice",
            status=CommandStatus.PENDING.value,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await db.save_command(command)
        background_tasks.add_task(mdm_client.restart_device, device_id)
        
        return {"status": "restart_sent", "device_id": device_id}
    except Exception as e:
        logger.error(f"Restart device error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Application Endpoints ====================

@app.post("/api/devices/{device_id}/apps/install")
async def install_app(
    device_id: str,
    request: InstallAppRequest,
    background_tasks: BackgroundTasks
):
    """Install application on device"""
    try:
        if not mdm_client:
            raise HTTPException(status_code=400, detail="MDM Client not configured")
        
        app = AppConfig(
            app_id=request.app_id,
            app_name=request.app_name,
            app_url=request.app_url,
            version=request.version,
            required=request.required,
            auto_update=request.auto_update
        )
        
        command = Command(
            device_id=device_id,
            command_type="InstallApplication",
            status=CommandStatus.PENDING.value,
            parameters={"app_id": request.app_id, "app_name": request.app_name},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await db.save_command(command)
        background_tasks.add_task(mdm_client.install_application, device_id, app)
        
        return {"status": "install_sent", "device_id": device_id, "app_id": request.app_id}
    except Exception as e:
        logger.error(f"Install app error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/devices/{device_id}/apps/{app_id}/remove")
async def remove_app(device_id: str, app_id: str, background_tasks: BackgroundTasks):
    """Remove application from device"""
    try:
        if not mdm_client:
            raise HTTPException(status_code=400, detail="MDM Client not configured")
        
        command = Command(
            device_id=device_id,
            command_type="RemoveApplication",
            status=CommandStatus.PENDING.value,
            parameters={"app_id": app_id},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await db.save_command(command)
        background_tasks.add_task(mdm_client.remove_application, device_id, app_id)
        
        return {"status": "remove_sent", "device_id": device_id, "app_id": app_id}
    except Exception as e:
        logger.error(f"Remove app error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Configuration Endpoints ====================

@app.post("/api/devices/{device_id}/security-config")
async def apply_security_config(
    device_id: str,
    request: SecurityConfigRequest,
    background_tasks: BackgroundTasks
):
    """Apply security configuration"""
    try:
        if not mdm_client:
            raise HTTPException(status_code=400, detail="MDM Client not configured")
        
        command = Command(
            device_id=device_id,
            command_type="SecurityConfiguration",
            status=CommandStatus.PENDING.value,
            parameters=request.settings,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await db.save_command(command)
        background_tasks.add_task(
            mdm_client.apply_security_config,
            device_id,
            request.settings
        )
        
        return {"status": "config_sent", "device_id": device_id}
    except Exception as e:
        logger.error(f"Apply security config error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Helper Functions ====================

async def execute_mdm_command(
    command_id: str,
    device_id: str,
    command_type: str,
    parameters: Optional[Dict[str, Any]]
):
    """Execute MDM command in background"""
    try:
        # Update command status
        await db.update_command_status(command_id, CommandStatus.EXECUTING.value)
        logger.info(f"Executing command: {command_id}")
        
        # Execute command based on type
        if command_type == "DeviceLock":
            result = mdm_client.lock_device(device_id, parameters.get("passcode"))
        elif command_type == "DeviceUnlock":
            result = mdm_client.unlock_device(device_id)
        elif command_type == "EraseDevice":
            result = mdm_client.wipe_device(device_id, parameters.get("pin"))
        elif command_type == "RestartDevice":
            result = mdm_client.restart_device(device_id)
        else:
            result = {"status": "unknown_command"}
        
        # Update command status
        await db.update_command_status(command_id, CommandStatus.COMPLETED.value, result)
        logger.info(f"Command completed: {command_id}")
    
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        await db.update_command_status(command_id, CommandStatus.FAILED.value, {"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
