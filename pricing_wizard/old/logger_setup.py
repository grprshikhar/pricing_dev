
import datetime
import getpass
import io
import logging
import logging.handlers
import sys
import traceback
from sqlite import sqlite

class TqdmToLogger(io.StringIO):
    """ Output stream for tqdm which will output to logger instead of stdout """

    def __init__(self, logger, level=logging.INFO, silent=False):
        """
        logger: Logger object
        level: Logging level whix is used for messages
        silent: Supresses any output if True
        """
        super().__init__()
        self.logger = logger
        self.level = level
        self.silent = silent
        self.buffer = io.StringIO()

    def write(self, string):
        """ Write string to buffer and strip newlines and tabs """
        if not self.silent:
            self.buffer.write(string.strip('\r\n\t'))

    def flush(self):
        """ Output content of buffer to logger """
        if not self.silent:
            self.logger.log(self.level, self.buffer.getvalue())
            self.buffer = io.StringIO()

class SQLiteHandler(logging.Handler):
    """  Class is child of class logging.Handler and writes logs to SQLite database """
    # Table where logs are stored
    table = 'logs'

    def __init__(self, filename):
        """
        filename: Path to database
        """
        super().__init__()
        # Establish connection to database
        self.database = sqlite.connect(filename)
        # Create table for logs if it does not exist
        self.database.execute(
            """
            CREATE TABLE IF NOT EXISTS {}(
                user_name TEXT,
                created_at TIMESTAMP,
                logger_name TEXT,
                level_no INTEGER,
                level_name TEXT,
                message TEXT,
                exception TEXT
            )
            """.format(sqlite.quote_identifier(type(self).table))
        )
        self.database.commit()

    # Overwrite method from parent class
    def emit(self, record):
        """ Emit a log record
        Record: logging.LogRecord object
        """
        self.acquire()
        try:
            self.database.execute(
                """
                INSERT INTO {}(
                    user_name,
                    created_at,
                    logger_name,
                    level_no,
                    level_name,
                    message,
                    exception
                )
                VALUES(?, ?, ?, ?, ?, ?, ?)
                """.format(sqlite.quote_identifier(type(self).table)), (
                    getpass.getuser(),
                    datetime.datetime.fromtimestamp(record.created),
                    record.name,
                    record.levelno,
                    record.levelname,
                    record.getMessage(),
                    self.format_exception(record.exc_info)
                )
            )
            self.database.commit()
        except Exception:
            self.handleError(record)
        finally:
            self.release()

    @staticmethod
    def format_exception(exc_info):
        """ Formats exception from LogRecord in the same way as it is done by logging module """
        if exc_info:
            sio = io.StringIO()
            traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], None, sio)
            string = sio.getvalue()
            sio.close()
            return string.strip()
        return None

    # Overwrite method from parent class
    def close(self):
        """ Closes connection to database """
        self.acquire()
        try:
            self.database.commit()
            self.database.close()
            super().close()
        finally:
            self.release()

class CountLogger(logging.Logger):
    """ Class is child of class logging.Logger to count how often message with a certain log levels
        are written. The counting works globally since we use a class variable.
    """
    # Class variable to store counts for log levels
    counts = {logging.DEBUG: 0, logging.INFO: 0, logging.WARNING: 0, logging.ERROR: 0,
              logging.CRITICAL: 0}

    # Overwrite method from parent class
    def callHandlers(self, record):
        """ Call the handlers for the specified record.
            Additionally, the counter for the corresponding log level is increased.
        """
        if record.levelno in type(self).counts:
            type(self).counts[record.levelno] += 1
        super().callHandlers(record)

    @classmethod
    def reset_counts(cls):
        """ Resets all counts """
        for count in cls.counts:
            cls.counts[count] = 0

    @property
    def debug_count(self):
        """ Returns number of DEBUG messages """
        return type(self).counts[logging.DEBUG]

    @property
    def info_count(self):
        """ Returns number of INFO messages """
        return type(self).counts[logging.INFO]

    @property
    def warning_count(self):
        """ Returns number of WARNING messages """
        return type(self).counts[logging.WARNING]

    @property
    def error_count(self):
        """ Returns number of ERROR messages """
        return type(self).counts[logging.ERROR]

    @property
    def critical_count(self):
        """ Returns number of CRITICAL messages """
        return type(self).counts[logging.CRITICAL]

    @property
    def warnings_or_higher(self):
        """ Returns whether there were messages with level WARNING or higher """
        return self.warning_count + self.error_count + self.critical_count > 0

class LessThanEqualFilter(logging.Filter):
    """ Filter class that allows logging only up to a certain level """
    def __init__(self, max_level, name=''):
        """
        max_level: maximum logging level (inclusive)
        name: argument of base class logging.Filter
        """
        super().__init__(name)
        self.max_level = max_level

    def filter(self, record):
        """ record: logging.LogRecord object """
        return record.levelno <= self.max_level

def logger_setup(console_level, log_file=None, file_level=logging.NOTSET, rotating=False,
                 backup_count=5, max_bytes=10*1024*1024, sqlite_file=None,
                 sqlite_level=logging.NOTSET, logger_class=CountLogger):
    """ Sets up the logger
    console_level: Logging level for console output
    log_file: Path to log file
    file_level: Logging level for file output
    rotating: If True, a rotating file handler will be used which appends log entires to a file
        up until a certain file size is reached after which a new log file is opened and the old one
        is saved by appending '.1'
    backup_count: Only used if rotating=True; old log files will be saved by appending the
        extensions '.1', '.2', etc. up until backup_count
    max_bytes: Only used if rotating=True; limits the size of the log file. If the limit is reached
        a new log file is opened
    sqlite_file: Path to file for logging to SQLite database
    sqlite_level: Logging level for sqlite output
    logger_class: Class to be used for logging. Allows to use custom subclasses for logging.
    """
    # Overwrite defaults in logging module
    logging.setLoggerClass(logger_class)
    logging.root = logger_class('root', logging.DEBUG)
    logging.Logger.root = logging.root
    logging.Logger.manager = logging.Manager(logging.Logger.root)
    # Get root logger
    logger = logging.getLogger()
    # Format of logging output
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                  '%Y-%m-%d %H:%M:%S')
    # Create console handler for stdout which logs only INFO and lower
    conh1 = logging.StreamHandler(sys.stdout)
    conh1.setLevel(console_level)
    conh1.setFormatter(formatter)
    conh1.addFilter(LessThanEqualFilter(logging.INFO))
    logger.addHandler(conh1)
    # Create console handler for stderr which logs only WARNING and higher
    conh2 = logging.StreamHandler(sys.stderr)
    conh2.setLevel(logging.WARNING)
    conh2.setFormatter(formatter)
    logger.addHandler(conh2)
    # Create file handler
    if log_file is not None:
        if rotating:
            fileh = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=max_bytes,
                                                         backupCount=backup_count, encoding='utf-8')
        else:
            fileh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        fileh.setLevel(file_level)
        fileh.setFormatter(formatter)
        logger.addHandler(fileh)
    # Create sqlite handler
    if sqlite_file is not None:
        sqlh = SQLiteHandler(sqlite_file)
        sqlh.setLevel(sqlite_level)
        logger.addHandler(sqlh)
