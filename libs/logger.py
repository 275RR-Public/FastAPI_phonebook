import logging

class AuditLogger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log(self, user: str, action: str, details: str = ""):
        message = f"User: {user} - Action: {action}"
        if details:
            message += f" - {details}"
        self.logger.info(message)

def setup_audit_logger(log_file: str = 'audit.log') -> logging.Logger:
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)
    if not audit_logger.handlers:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        audit_logger.addHandler(handler)
    return audit_logger

def get_audit_logger() -> AuditLogger:
    logger = setup_audit_logger()
    return AuditLogger(logger)