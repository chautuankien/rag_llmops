import logging
import os
import sys
import time
import threading
import inspect
import datetime
from pathlib import Path
from typing import Dict, Optional, Union, List, Callable


class LoggerSingleton:
    """
    A Singleton Logger class for the Feature Pipeline system.
    Ensures only one logger instance exists across all pipeline components.
    Thread-safe implementation to support separate pipeline execution.
    """
    _instance = None
    _lock = threading.Lock()
    _loggers = {}  # Store loggers by name

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LoggerSingleton, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, log_dir: str = "logs", default_level: int = logging.INFO, 
                 log_format: str|None = None, date_format: str|None = None):
        """
        Initialize the LoggerSingleton.
        
        Args:
            log_dir: Directory to store log files
            default_level: Default logging level
            log_format: Custom log format
            date_format: Custom date format for logs
        """
        with self._lock:
            if self._initialized:
                return
                
            self.log_dir = log_dir
            self.default_level = default_level
            
            # Create log directory if it doesn't exist
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # Set default formats if not provided
            self.log_format = log_format or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            self.date_format = date_format or '%Y-%m-%d %H:%M:%S'
            
            # Configure root logger
            logging.basicConfig(
                level=self.default_level,
                format=self.log_format,
                datefmt=self.date_format
            )
            
            self._initialized = True
    
    def get_logger(self, name: str, level: int|None = None, 
                  to_file: bool = True, to_console: bool = True) -> logging.Logger:
        """
        Get a logger by name. If it doesn't exist, create it.
        
        Args:
            name: Name of the logger (typically the component/class name)
            level: Logging level for this logger
            to_file: Whether to log to a file
            to_console: Whether to log to console
            
        Returns:
            A configured logger instance
        """
        with self._lock:
            # Return existing logger if already created
            if name in self._loggers:
                return self._loggers[name]
            
            # Create a new logger
            logger = logging.getLogger(name)
            level = level or self.default_level
            if level is not None:
                logger.setLevel(level)
            logger.propagate = False  # Prevent duplicate logs
            
            # Clear any existing handlers
            if logger.handlers:
                logger.handlers.clear()
            
            # Add handlers based on configuration
            if to_console:
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(logging.Formatter(self.log_format, self.date_format))
                logger.addHandler(console_handler)
            
            if to_file:
                # Create unique log file for this logger
                timestamp = datetime.now().strftime("%Y%m%d")
                log_file = os.path.join(self.log_dir, f"{name}_{timestamp}.log")
                
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(logging.Formatter(self.log_format, self.date_format))
                logger.addHandler(file_handler)
            
            # Store and return the logger
            self._loggers[name] = logger
            return logger
    
    def configure_from_dict(self, config: dict):
        """
        Configure logger from a dictionary configuration.
        
        Args:
            config: Dictionary with logger configuration
        """
        with self._lock:
            if 'log_dir' in config:
                self.log_dir = config['log_dir']
                if not os.path.exists(self.log_dir):
                    os.makedirs(self.log_dir)
            
            if 'default_level' in config:
                level_name = config['default_level'].upper()
                self.default_level = getattr(logging, level_name, logging.INFO)
            
            if 'log_format' in config:
                self.log_format = config['log_format']
            
            if 'date_format' in config:
                self.date_format = config['date_format']
                
    def set_level_for_all(self, level: int):
        """
        Set the same logging level for all existing loggers.
        
        Args:
            level: The logging level to set
        """
        with self._lock:
            for logger in self._loggers.values():
                logger.setLevel(level)
                
    def flush_all(self):
        """Flush all loggers (useful before application exit)"""
        with self._lock:
            for logger in self._loggers.values():
                for handler in logger.handlers:
                    handler.flush()

class ColorFormatter(logging.Formatter):
    """Custom formatter with colored output for console"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[41m',  # Red background
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_message = super().format(record)
        if record.levelname in self.COLORS:
            # Add color to the level name only
            colored_level = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            log_message = log_message.replace(record.levelname, colored_level)
        return log_message


class Logger:
    """
    A singleton logger implementation with custom formatting.
    Thread-safe and provides both console and file logging.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Logger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, log_dir: str = "logs", 
                 level: str = "DEBUG", 
                 rotation: str = "1 day",
                 retention: str = "30 days",
                 enable_console: bool = True,
                 enable_file: bool = True):
        """
        Initialize the logger singleton.
        
        Args:
            log_dir: Directory to store log files
            level: Default logging level
            rotation: When to rotate logs (size or time-based)
            retention: How long to keep log files
            enable_console: Whether to log to console
            enable_file: Whether to log to file
        """
        with self._lock:
            if self._initialized:
                return
                
            # Store configuration
            self.log_dir = log_dir
            self.level = self._parse_level(level)
            self.rotation = rotation
            self.retention = retention
            self.enable_console = enable_console
            self.enable_file = enable_file
            
            # Create log directory
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            # Initialize root logger
            self.logger = logging.getLogger("root_logger")
            self.logger.setLevel(self.level)
            self.logger.propagate = False
            
            # Clear existing handlers
            if self.logger.handlers:
                for handler in self.logger.handlers:
                    handler.close()
                self.logger.handlers.clear()
            
            # Log format
            self.log_format = "{asctime} | {levelname:<8} | {module}:{funcName}:{lineno} - {message}"
            self.date_format = "%Y-%m-%d %H:%M:%S.%f"
            
            # Setup handlers
            if enable_console:
                self._add_console_handler()
            
            if enable_file:
                self._add_file_handler()
            
            # Set up log levels as methods (like loguru)
            self._initialized = True

    def _add_console_handler(self):
        """Add a handler for console output with colors"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        
        # Use color formatter for console
        formatter = ColorFormatter(
            fmt=self.log_format,
            datefmt=self.date_format,
            style='{'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """Add a handler for file output"""
        # Create a dated log file
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"logfile_{today}.log")
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.level)
        
        # Use standard formatter for file
        formatter = logging.Formatter(
            fmt=self.log_format,
            datefmt=self.date_format,
            style='{'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _parse_level(self, level: Union[str, int]) -> int:
        """Parse logging level from string or int"""
        if isinstance(level, str):
            return getattr(logging, level.upper(), logging.INFO)
        return level
    
    def _log(self, level: int, message: str, *args, **kwargs):
        """
        Log a message with the given level, capturing correct caller information
        """
        # Get the frame of the caller (skipping this function and the level-specific methods)
        frame = inspect.currentframe().f_back.f_back
        
        # Create a custom record with caller's information
        record = logging.LogRecord(
            name=self.logger.name,
            level=level,
            pathname=frame.f_code.co_filename,
            lineno=frame.f_lineno,
            msg=message,
            args=args,
            exc_info=kwargs.get('exc_info'),
            func=frame.f_code.co_name,
            sinfo=None
        )
        
        # Handle the record directly to preserve call site information
        for handler in self.logger.handlers:
            if record.levelno >= handler.level:
                handler.handle(record)
    
    # Level-specific methods
    def debug(self, message, *args, **kwargs):
        self._log(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        self._log(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        self._log(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        self._log(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        self._log(logging.CRITICAL, message, *args, **kwargs)
    
    def exception(self, message, *args, **kwargs):
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, *args, **kwargs)
    
    # Flush and close handlers
    def flush(self):
        """Flush all handlers"""
        for handler in self.logger.handlers:
            handler.flush()
    
    def close(self):
        """Close all handlers"""
        for handler in self.logger.handlers:
            handler.close()
        self.logger.handlers.clear()


# Create a global instance
logger = Logger(log_dir="logs")
