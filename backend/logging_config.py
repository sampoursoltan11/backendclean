"""
Logging configuration for TRA system
Saves all logs to a file for easy debugging
"""
import logging
import sys
from pathlib import Path

def setup_logging(log_file='logs/tra_system.log'):
    """
    Set up logging to both console and file.
    
    Args:
        log_file: Path to log file (relative to project root)
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter('%(message)s')
    
    # File handler (detailed logs)
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler (simple format for readability)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # Also capture print statements to file
    class PrintLogger:
        def __init__(self, logger, level):
            self.logger = logger
            self.level = level
            
        def write(self, message):
            if message.strip():
                self.logger.log(self.level, message.strip())
                
        def flush(self):
            pass
    
    print(f"✅ Logging configured: Console + File ({log_file})")
    return log_file
