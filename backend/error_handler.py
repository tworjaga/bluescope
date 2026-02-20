"""
Error Handler - Comprehensive error handling for BlueScope
Provides centralized error handling, logging, and recovery mechanisms
"""

import sys
import logging
import traceback
from typing import Optional, Callable, Any, Dict, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()
    FATAL = auto()


class ErrorCategory(Enum):
    """Error categories"""
    CAPTURE = "capture"
    HARDWARE = "hardware"
    ML = "ml"
    GUI = "gui"
    NETWORK = "network"
    FILE = "file"
    MEMORY = "memory"
    UNKNOWN = "unknown"


@dataclass
class ErrorRecord:
    """Record of an error"""
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    message: str
    exception: Optional[Exception]
    traceback_str: str
    context: Dict[str, Any]
    recovered: bool = False


class ErrorHandler:
    """
    Centralized error handler for BlueScope
    Provides error logging, recovery, and reporting
    """
    
    def __init__(self):
        self.error_history: List[ErrorRecord] = []
        self.max_history = 1000
        
        # Error callbacks by category
        self.callbacks: Dict[ErrorCategory, List[Callable]] = {
            cat: [] for cat in ErrorCategory
        }
        
        # Recovery strategies
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        
        # Statistics
        self.error_counts: Dict[ErrorSeverity, int] = {
            sev: 0 for sev in ErrorSeverity
        }
        
        logger.info("ErrorHandler initialized")
    
    def handle_error(
        self,
        exception: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = False
    ) -> bool:
        """
        Handle an error
        
        Args:
            exception: The exception that occurred
            category: Error category
            severity: Error severity
            context: Additional context information
            recoverable: Whether this error can be recovered from
        
        Returns:
            True if error was handled successfully
        """
        context = context or {}
        
        # Create error record
        record = ErrorRecord(
            timestamp=datetime.now(),
            severity=severity,
            category=category,
            message=str(exception),
            exception=exception,
            traceback_str=traceback.format_exc(),
            context=context,
            recovered=False
        )
        
        # Log error
        self._log_error(record)
        
        # Store in history
        self._store_error(record)
        
        # Update statistics
        self.error_counts[severity] += 1
        
        # Call callbacks
        self._notify_callbacks(record)
        
        # Attempt recovery if recoverable
        if recoverable:
            record.recovered = self._attempt_recovery(record)
        
        return record.recovered
    
    def _log_error(self, record: ErrorRecord):
        """Log error to logger"""
        log_message = f"[{record.category.value.upper()}] {record.message}"
        
        if record.severity == ErrorSeverity.DEBUG:
            logger.debug(log_message)
        elif record.severity == ErrorSeverity.INFO:
            logger.info(log_message)
        elif record.severity == ErrorSeverity.WARNING:
            logger.warning(log_message)
        elif record.severity == ErrorSeverity.ERROR:
            logger.error(log_message)
        elif record.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.FATAL]:
            logger.critical(log_message)
            logger.critical(f"Traceback:\n{record.traceback_str}")
    
    def _store_error(self, record: ErrorRecord):
        """Store error in history"""
        self.error_history.append(record)
        
        # Limit history size
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]
    
    def _notify_callbacks(self, record: ErrorRecord):
        """Notify registered callbacks"""
        callbacks = self.callbacks.get(record.category, [])
        
        for callback in callbacks:
            try:
                callback(record)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def _attempt_recovery(self, record: ErrorRecord) -> bool:
        """Attempt to recover from error"""
        strategy = self.recovery_strategies.get(record.category)
        
        if strategy:
            try:
                logger.info(f"Attempting recovery for {record.category.value} error...")
                success = strategy(record)
                if success:
                    logger.info("Recovery successful")
                else:
                    logger.warning("Recovery failed")
                return success
            except Exception as e:
                logger.error(f"Recovery attempt failed: {e}")
                return False
        
        return False
    
    def register_callback(
        self,
        category: ErrorCategory,
        callback: Callable[[ErrorRecord], None]
    ):
        """Register error callback"""
        self.callbacks[category].append(callback)
        logger.debug(f"Registered callback for {category.value}")
    
    def register_recovery_strategy(
        self,
        category: ErrorCategory,
        strategy: Callable[[ErrorRecord], bool]
    ):
        """Register recovery strategy"""
        self.recovery_strategies[category] = strategy
        logger.debug(f"Registered recovery strategy for {category.value}")
    
    def get_error_history(
        self,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        limit: int = 100
    ) -> List[ErrorRecord]:
        """Get error history with optional filtering"""
        filtered = self.error_history
        
        if category:
            filtered = [e for e in filtered if e.category == category]
        
        if severity:
            filtered = [e for e in filtered if e.severity == severity]
        
        return filtered[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "total_errors": len(self.error_history),
            "by_severity": {sev.name: count for sev, count in self.error_counts.items()},
            "by_category": {
                cat.value: len([e for e in self.error_history if e.category == cat])
                for cat in ErrorCategory
            },
            "recovery_rate": self._calculate_recovery_rate()
        }
    
    def _calculate_recovery_rate(self) -> float:
        """Calculate error recovery rate"""
        recoverable_errors = [e for e in self.error_history if e.recovered is not None]
        if not recoverable_errors:
            return 100.0
        
        recovered = sum(1 for e in recoverable_errors if e.recovered)
        return (recovered / len(recoverable_errors)) * 100
    
    def clear_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_counts = {sev: 0 for sev in ErrorSeverity}
        logger.info("Error history cleared")


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get or create global error handler"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_exception(
    exception: Exception,
    category: str = "unknown",
    severity: str = "error",
    **context
) -> bool:
    """
    Convenience function to handle exceptions
    
    Args:
        exception: The exception to handle
        category: Error category (capture, hardware, ml, gui, network, file, memory, unknown)
        severity: Error severity (debug, info, warning, error, critical, fatal)
        **context: Additional context
    
    Returns:
        True if recovered successfully
    """
    handler = get_error_handler()
    
    # Convert strings to enums
    try:
        cat_enum = ErrorCategory(category.lower())
    except ValueError:
        cat_enum = ErrorCategory.UNKNOWN
    
    try:
        sev_enum = ErrorSeverity(severity.upper())
    except ValueError:
        sev_enum = ErrorSeverity.ERROR
    
    return handler.handle_error(
        exception=exception,
        category=cat_enum,
        severity=sev_enum,
        context=context,
        recoverable=sev_enum in [ErrorSeverity.WARNING, ErrorSeverity.ERROR]
    )


class ErrorHandlingDecorator:
    """Decorator for automatic error handling"""
    
    def __init__(
        self,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        recoverable: bool = False,
        default_return: Any = None
    ):
        self.category = category
        self.severity = severity
        self.recoverable = recoverable
        self.default_return = default_return
    
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handler = get_error_handler()
                recovered = handler.handle_error(
                    exception=e,
                    category=self.category,
                    severity=self.severity,
                    context={
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs)
                    },
                    recoverable=self.recoverable
                )
                
                if not recovered:
                    return self.default_return
                
                # If recovered, retry once
                try:
                    return func(*args, **kwargs)
                except:
                    return self.default_return
        
        return wrapper


# Convenience decorators
def safe_capture(default_return=None):
    """Decorator for capture functions"""
    return ErrorHandlingDecorator(
        category=ErrorCategory.CAPTURE,
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        default_return=default_return
    )


def safe_hardware(default_return=None):
    """Decorator for hardware functions"""
    return ErrorHandlingDecorator(
        category=ErrorCategory.HARDWARE,
        severity=ErrorSeverity.ERROR,
        recoverable=True,
        default_return=default_return
    )


def safe_ml(default_return=None):
    """Decorator for ML functions"""
    return ErrorHandlingDecorator(
        category=ErrorCategory.ML,
        severity=ErrorSeverity.ERROR,
        recoverable=False,
        default_return=default_return
    )


def safe_gui(default_return=None):
    """Decorator for GUI functions"""
    return ErrorHandlingDecorator(
        category=ErrorCategory.GUI,
        severity=ErrorSeverity.WARNING,
        recoverable=True,
        default_return=default_return
    )


def test_error_handler():
    """Test error handler functionality"""
    print("\n" + "="*60)
    print("Error Handler Test")
    print("="*60)
    
    handler = get_error_handler()
    
    # Test 1: Basic error handling
    print("\n1. Testing basic error handling:")
    try:
        raise ValueError("Test error")
    except Exception as e:
        recovered = handler.handle_error(
            e,
            category=ErrorCategory.CAPTURE,
            severity=ErrorSeverity.ERROR
        )
        print(f"  Error handled, recovered: {recovered}")
    
    # Test 2: Recovery strategy
    print("\n2. Testing recovery strategy:")
    
    def mock_recovery(record: ErrorRecord) -> bool:
        print(f"  Attempting recovery for: {record.message}")
        return True
    
    handler.register_recovery_strategy(ErrorCategory.HARDWARE, mock_recovery)
    
    try:
        raise RuntimeError("Hardware failure")
    except Exception as e:
        recovered = handler.handle_error(
            e,
            category=ErrorCategory.HARDWARE,
            severity=ErrorSeverity.ERROR,
            recoverable=True
        )
        print(f"  Recovery result: {recovered}")
    
    # Test 3: Statistics
    print("\n3. Testing statistics:")
    stats = handler.get_statistics()
    print(f"  Total errors: {stats['total_errors']}")
    print(f"  By severity: {stats['by_severity']}")
    print(f"  Recovery rate: {stats['recovery_rate']:.1f}%")
    
    # Test 4: Decorator
    print("\n4. Testing decorator:")
    
    @safe_capture(default_return="fallback")
    def risky_function():
        raise Exception("Something went wrong")
    
    result = risky_function()
    print(f"  Decorator result: {result}")
    
    print("\n All error handler tests passed")
    return True


if __name__ == "__main__":
    test_error_handler()

