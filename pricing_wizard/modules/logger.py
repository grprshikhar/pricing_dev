# Build a logging device which could use google cloud for storage
# See more here...
# ... https://lynn-kwong.medium.com/stop-using-print-in-your-python-code-for-logging-use-the-logging-module-like-a-pro-66fb0427d636
# ... https://levelup.gitconnected.com/how-to-write-logs-to-google-cloud-logging-in-python-46e7b514c60b

import logging
import google.cloud.logging
from google.cloud.logging.handlers import CloudLoggingHandler


# You can customize the formatter according to your needs.
FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
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
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(FORMATTER)
    return file_handler

# Cloud handler - Stream to Google
def get_gcloud_handler(logger_name):
    client = google.cloud.logging.Client.from_service_account_json("path_to_json")
    client.setup_logging()
    gcloud_logging_handler = CloudLoggingHandler(client, name=logger_name+".log")
    return gcloud_logging_handler


def get_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    logger.addHandler(get_stream_handler())
    logger.addHandler(get_file_handler(logger_name))
    logger.addHandler(get_gcloud_handler(logger_name))

    return logger