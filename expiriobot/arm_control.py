"""
Robotic arm control module for ExpirioBot.
Supports both physical DOFBOT arm and mock mode for testing.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

from .config import get_config, ArmConfig

logger = logging.getLogger(__name__)


@dataclass
class ArmPosition:
    """Represents a named arm position with servo angles."""
    name: str
    angles: List[int]


class ArmDevice(ABC):
    """Abstract base class for arm devices."""
    
    @abstractmethod
    def write_servo(self, servo_id: int, angle: int, duration: int) -> None:
        """Write angle to a specific servo."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass


class PhysicalArmDevice(ArmDevice):
    """Physical DOFBOT arm device using Arm_Lib."""
    
    def __init__(self):
        try:
            from Arm_Lib import Arm_Device
            self.arm = Arm_Device()
            time.sleep(0.1)
            logger.info("Physical arm device initialized")
        except ImportError as e:
            raise RuntimeError(f"Arm_Lib not available: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize physical arm: {e}")
    
    def write_servo(self, servo_id: int, angle: int, duration: int) -> None:
        self.arm.Arm_serial_servo_write(servo_id, angle, duration)
    
    def cleanup(self) -> None:
        try:
            del self.arm
            logger.info("Physical arm device cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up physical arm: {e}")


class MockArmDevice(ArmDevice):
    """Mock arm device for testing without physical hardware."""
    
    def __init__(self):
        logger.warning("Mock Arm Device initialized (no physical arm connected)")
    
    def write_servo(self, servo_id: int, angle: int, duration: int) -> None:
        logger.info(f"[MOCK ARM] Servo {servo_id} -> Position {angle} (Duration: {duration}ms)")
    
    def cleanup(self) -> None:
        logger.info("Mock Arm Device cleaned up")


class ArmController:
    """Main arm controller that manages arm movements."""
    
    def __init__(self, mock: bool = False, config: Optional[ArmConfig] = None):
        self.config = config or get_config().arm
        self.mock = mock
        self.arm: ArmDevice
        self._last_position: Optional[str] = None
        
        if mock:
            self.arm = MockArmDevice()
        else:
            try:
                self.arm = PhysicalArmDevice()
            except RuntimeError as e:
                logger.warning(f"Failed to initialize physical arm: {e}. Falling back to mock mode.")
                self.mock = True
                self.arm = MockArmDevice()
        
        self._positions = {
            name: ArmPosition(name, angles)
            for name, angles in self.config.positions.items()
        }
    
    def _get_adjusted_time(self, servo_id: int, base_time: int) -> int:
        """Calculate adjusted time for specific servos."""
        if servo_id == 5:
            return int(base_time * self.config.servo_5_time_factor)
        elif servo_id == 1:
            return int(base_time * self.config.servo_1_time_factor)
        return base_time
    
    def clamp(self, enable: bool) -> None:
        """Control the arm clamp."""
        position = self.config.clamp_close if enable else self.config.clamp_open
        action = "CLOSE" if enable else "OPEN"
        logger.info(f"[ARM] Clamp: {action}")
        self.arm.write_servo(6, position, 400)
        time.sleep(0.5)
    
    def move_to(self, position_name: str, duration: Optional[int] = None) -> bool:
        """Move arm to a predefined position."""
        if position_name not in self._positions:
            logger.error(f"Unknown position: {position_name}")
            return False
        
        position = self._positions[position_name]
        move_time = duration or self.config.move_time_default
        
        logger.info(f"[ARM] Moving to {position_name}: {position.angles}")
        
        for i, angle in enumerate(position.angles):
            servo_id = i + 1
            adjusted_time = self._get_adjusted_time(servo_id, move_time)
            self.arm.write_servo(servo_id, angle, adjusted_time)
            time.sleep(0.01)
        
        time.sleep(move_time / 1000)
        self._last_position = position_name
        return True
    
    def move_sequence(self, sequence: List[tuple[str, Optional[int]]]) -> bool:
        """Execute a sequence of movements."""
        for position_name, duration in sequence:
            if not self.move_to(position_name, duration):
                return False
        return True
    
    def pick_and_place(self, target: str) -> bool:
        """
        Execute pick and place operation.
        
        Args:
            target: 'left' or 'right'
        
        Returns:
            True if successful, False otherwise
        """
        if target not in ("left", "right"):
            logger.error(f"Invalid target: {target}. Use 'left' or 'right'.")
            return False
        
        logger.info(f"[ARM] Starting pick and place to {target.upper()}")
        
        try:
            # Pick up sequence
            self.clamp(False)  # Open clamp
            self.move_to("front", self.config.move_time_pickup)
            self.clamp(True)   # Close clamp
            self.move_to("top", self.config.move_time_transition)
            
            # Move to target
            self.move_to(target, self.config.move_time_pickup)
            self.clamp(False)  # Release object
            self.move_to(f"{target}_top", self.config.move_time_release)
            
            # Return to rest
            self.move_to("top", self.config.move_time_transition)
            self.move_to("rest", self.config.move_time_pickup)
            
            logger.info(f"[ARM] Pick and place to {target.upper()} complete")
            return True
            
        except Exception as e:
            logger.error(f"Error during pick and place: {e}")
            return False
    
    def go_to_rest(self) -> bool:
        """Move arm to rest position."""
        return self.move_to("rest", self.config.move_time_pickup)
    
    def cleanup(self) -> None:
        """Clean up arm resources."""
        self.arm.cleanup()


def create_arm_controller(mock: bool = False) -> ArmController:
    """Factory function to create arm controller."""
    return ArmController(mock=mock)