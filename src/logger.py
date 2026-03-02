import logging
import logging.handlers
import os

def setup_logger(log_file="coolsync.log", level=logging.INFO):
    """Set up the application logger with console and rotating file handlers."""
    logger = logging.getLogger("coolToReminder")
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # Log format
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (Rotating: 5 MB per file, keep 3 backups)
    # We put the log in a logs directory
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", log_file)
    
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create a default logger instance
logger = setup_logger()
