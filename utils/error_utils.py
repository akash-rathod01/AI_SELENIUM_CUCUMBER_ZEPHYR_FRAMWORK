# utils/error_utils.py
from loguru import logger

class ErrorUtils:
    @staticmethod
    def log_and_raise(error_msg, exception_type=Exception):
        logger.error(error_msg)
        raise exception_type(error_msg)

    @staticmethod
    def safe_execute(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error executing {func.__name__}: {e}")
            return None
