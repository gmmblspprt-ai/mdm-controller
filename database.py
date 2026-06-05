"""
MongoDB Database Integration for MDM
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import os
import logging
import uuid

logger = logging.getLogger(__name__)


class DeviceStatus(Enum):
    """Device status enum"""
    ENROLLED = "enrolled"
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOST = "lost"
    RETIRED = "retired"


class CommandStatus(Enum):
    """Command status enum"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Device:
    """Device model"""
    device_id: str
    device_name: str
    platform: str
    model: Optional[str] = None
    os_version: Optional[str] = None
    serial_number: Optional[str] = None
    status: str = field(default=DeviceStatus.ENROLLED.value)
    last_checkin: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Command:
    """Command model"""
    device_id: str
    command_type: str
    status: str = field(default=CommandStatus.PENDING.value)
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parameters: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Configuration:
    """Configuration model"""
    config_id: str
    device_id: str
    config_type: str
    settings: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class MongoDB:
    """MongoDB database handler"""

    def __init__(
        self,
        uri: Optional[str] = None,
        db_name: str = "mdm_controller"
    ):
        """
        Initialize MongoDB connection
        
        Args:
            uri: MongoDB connection URI
            db_name: Database name
        """
        self.uri = uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = db_name
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(self.uri)
            self.db = self.client[self.db_name]
            
            # Test connection
            await self.client.admin.command("ping")
            logger.info(f"Connected to MongoDB: {self.db_name}")
            
            # Create indexes
            await self._create_indexes()
        except Exception as e:
            logger.error(f"MongoDB connection error: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create database indexes"""
        try:
            # Device indexes
            await self.db.devices.create_index([("device_id", ASCENDING)], unique=True)
            await self.db.devices.create_index([("platform", ASCENDING)])
            await self.db.devices.create_index([("status", ASCENDING)])
            await self.db.devices.create_index([("created_at", DESCENDING)])
            
            # Command indexes
            await self.db.commands.create_index([("command_id", ASCENDING)], unique=True)
            await self.db.commands.create_index([("device_id", ASCENDING)])
            await self.db.commands.create_index([("status", ASCENDING)])
            await self.db.commands.create_index([("created_at", DESCENDING)])
            
            # Configuration indexes
            await self.db.configurations.create_index([("device_id", ASCENDING)])
            await self.db.configurations.create_index([("config_type", ASCENDING)])
            
            logger.info("Database indexes created")
        except Exception as e:
            logger.error(f"Index creation error: {e}")

    # ==================== Device Operations ====================

    async def save_device(self, device: Device):
        """Save device to database"""
        try:
            device_dict = asdict(device)
            await self.db.devices.update_one(
                {"device_id": device.device_id},
                {"$set": device_dict},
                upsert=True
            )
            logger.info(f"Device saved: {device.device_id}")
        except Exception as e:
            logger.error(f"Save device error: {e}")
            raise

    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get device from database"""
        try:
            device_dict = await self.db.devices.find_one({"device_id": device_id})
            if device_dict:
                device_dict.pop("_id", None)
                return Device(**device_dict)
            return None
        except Exception as e:
            logger.error(f"Get device error: {e}")
            raise

    async def get_devices(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Device]:
        """Get devices from database"""
        try:
            query = {}
            if platform:
                query["platform"] = platform
            if status:
                query["status"] = status
            
            devices = []
            cursor = self.db.devices.find(query).sort("created_at", -1)
            
            async for device_dict in cursor:
                device_dict.pop("_id", None)
                devices.append(Device(**device_dict))
            
            return devices
        except Exception as e:
            logger.error(f"Get devices error: {e}")
            raise

    async def delete_device(self, device_id: str):
        """Delete device from database"""
        try:
            result = await self.db.devices.delete_one({"device_id": device_id})
            if result.deleted_count > 0:
                logger.info(f"Device deleted: {device_id}")
            else:
                logger.warning(f"Device not found: {device_id}")
        except Exception as e:
            logger.error(f"Delete device error: {e}")
            raise

    async def update_device_status(self, device_id: str, status: str):
        """Update device status"""
        try:
            await self.db.devices.update_one(
                {"device_id": device_id},
                {
                    "$set": {
                        "status": status,
                        "updated_at": datetime.now(),
                        "last_checkin": datetime.now()
                    }
                }
            )
            logger.info(f"Device status updated: {device_id} -> {status}")
        except Exception as e:
            logger.error(f"Update device status error: {e}")
            raise

    # ==================== Command Operations ====================

    async def save_command(self, command: Command):
        """Save command to database"""
        try:
            command_dict = asdict(command)
            await self.db.commands.insert_one(command_dict)
            logger.info(f"Command saved: {command.command_id}")
        except Exception as e:
            logger.error(f"Save command error: {e}")
            raise

    async def get_command(self, command_id: str) -> Optional[Command]:
        """Get command from database"""
        try:
            command_dict = await self.db.commands.find_one({"command_id": command_id})
            if command_dict:
                command_dict.pop("_id", None)
                return Command(**command_dict)
            return None
        except Exception as e:
            logger.error(f"Get command error: {e}")
            raise

    async def get_device_commands(self, device_id: str) -> List[Command]:
        """Get commands for device"""
        try:
            commands = []
            cursor = self.db.commands.find({"device_id": device_id}).sort("created_at", -1)
            
            async for command_dict in cursor:
                command_dict.pop("_id", None)
                commands.append(Command(**command_dict))
            
            return commands
        except Exception as e:
            logger.error(f"Get device commands error: {e}")
            raise

    async def update_command_status(
        self,
        command_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ):
        """Update command status"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.now()
            }
            if result:
                update_data["result"] = result
            
            await self.db.commands.update_one(
                {"command_id": command_id},
                {"$set": update_data}
            )
            logger.info(f"Command status updated: {command_id} -> {status}")
        except Exception as e:
            logger.error(f"Update command status error: {e}")
            raise

    # ==================== Configuration Operations ====================

    async def save_configuration(self, config: Configuration):
        """Save configuration to database"""
        try:
            config_dict = asdict(config)
            await self.db.configurations.insert_one(config_dict)
            logger.info(f"Configuration saved: {config.config_id}")
        except Exception as e:
            logger.error(f"Save configuration error: {e}")
            raise

    async def get_device_configurations(self, device_id: str) -> List[Configuration]:
        """Get configurations for device"""
        try:
            configs = []
            cursor = self.db.configurations.find({"device_id": device_id})
            
            async for config_dict in cursor:
                config_dict.pop("_id", None)
                configs.append(Configuration(**config_dict))
            
            return configs
        except Exception as e:
            logger.error(f"Get device configurations error: {e}")
            raise
