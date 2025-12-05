
import logging
import sys
import os

def setup_logging(log_level=logging.INFO):
    """
    Configura el sistema de logging.
    """
    logger = logging.getLogger("athenas_lite")
    logger.setLevel(log_level)
    
    # Previene duplicar handlers si se llama varias veces
    if not logger.handlers:
        # Handler de consola
        c_handler = logging.StreamHandler(sys.stdout)
        c_handler.setLevel(log_level)
        
        # Formato
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        
        logger.addHandler(c_handler)
    
    return logger

logger = setup_logging()
