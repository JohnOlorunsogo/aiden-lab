"""Legacy logger service - now uses integrated ENSP logger service."""
from app.services.ensp_logger_service import ensp_logger_service

class HuaweiLoggerService:
    """
    Legacy service wrapper for backward compatibility.
    
    This now uses the integrated ENSP logger service instead of
    running as a subprocess. The service is automatically started
    in the application lifespan handler.
    """
    
    def start_logger(self):
        """
        Start Huawei logger (now uses integrated service).
        
        Note: The logger is automatically started in the application
        lifespan. This method is kept for backward compatibility.
        """
        # The service is already managed by the application lifespan
        # Just check if it's running
        if ensp_logger_service.is_running:
            return True
        # Try to start it if not running
        return ensp_logger_service.start()

# Backward compatibility alias
huawei_logger_service = HuaweiLoggerService()
