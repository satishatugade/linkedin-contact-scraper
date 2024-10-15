import logging
import inspect

def setup_logging():
    logging.basicConfig(
        filename='logs/contact_logs.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def log_message(message, level='info',error=None):

    caller_frame = inspect.stack()[1]
    caller_filename = caller_frame.filename
    caller_lineno = caller_frame.lineno

    if error:
        message = f"{message} - Error: {error}"

    message = f"{message} - [Caller: {caller_filename}:{caller_lineno}]"    
        
    if level == 'info':
        logging.info(message)
    elif level == 'debug':
        logging.debug(message)
    elif level == 'error':
        logging.error(message)
    else:
        logging.warning(f"Invalid log level: {level}. Message: {message}")
