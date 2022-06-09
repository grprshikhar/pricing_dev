# Build a logging device which could use google cloud for storage
# See more here...
# ... https://lynn-kwong.medium.com/stop-using-print-in-your-python-code-for-logging-use-the-logging-module-like-a-pro-66fb0427d636
# ... https://levelup.gitconnected.com/how-to-write-logs-to-google-cloud-logging-in-python-46e7b514c60b

import logging
import inspect
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler

class CallStackFormatter(logging.Formatter):

    def formatStack(self, _ = None) -> str:
        stack = inspect.stack()[::-1]
        stack_names = (inspect.getmodulename(stack[0].filename),
                       *(frame.function
                         for frame
                         in stack[1:-9]))
        if stack_names:
            return '::'.join([x for x in stack_names if x])
        else:
            return ""

    def format(self, record):
        record.message = record.getMessage()
        record.stack_info = self.formatStack()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        s = self.formatMessage(record)
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        return s

# You can customize the formatter according to your needs.
FORMATTER = CallStackFormatter(
    "%(asctime)s > %(name)s > %(levelname)s > %(stack_info)s > %(message)s"
)

# Stream handler - Stream to terminal
def get_stream_handler():
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(FORMATTER)
    return stream_handler

# File handler - Stream to file
def get_file_handler(logger_name):
    file_handler = logging.FileHandler(filename=logger_name+".log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(FORMATTER)
    return file_handler

# Cloud handler - Stream to Google
def get_gcloud_handler(logger_name):
    client = google.cloud.logging.Client.from_service_account_json("path_to_json")
    client.setup_logging()
    gcloud_logging_handler = CloudLoggingHandler(client, name=logger_name+".log")
    return gcloud_logging_handler

# We can only set the handlers once otherwise we get into thread issues with adding/removing
def get_logger(logger_name, to_terminal = False, to_file = False, to_cloud = False):
    # Create logger
    logger = logging.getLogger(logger_name)
    # Set logging level
    logger.setLevel(logging.INFO)
    # Logger is a singleton but handlers are NOT
    if logger.handlers:
        return logger
    # Only add handlers if we are creating the first instance
    if to_terminal:
        logger.addHandler(get_stream_handler())
    if to_file:
        logger.addHandler(get_file_handler(logger_name))
    if to_cloud:
        logger.addHandler(get_gcloud_handler(logger_name))

    return logger