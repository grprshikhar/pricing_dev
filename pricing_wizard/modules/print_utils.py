import sys
import traceback
from termcolor import colored
from tabulate import tabulate
from googleapiclient.errors import HttpError
from redshift_connector.error import InterfaceError, ProgrammingError
import modules.logger as logger

# Print utility
def print_check(msg):
    msg_fmt = " - "+colored(u'\u2713', 'green', attrs=['bold'])+" - "+colored(msg, 'blue')
    print( msg_fmt )
    logger.get_logger("pricing_wizard",to_file=True).info( msg_fmt )

def print_exclaim(msg):
    msg_fmt = " - "+colored('!', 'green', attrs=['bold'])+" - "+colored(msg, 'blue', attrs=['bold'])
    print( msg_fmt )
    logger.get_logger("pricing_wizard",to_file=True).info( msg_fmt )

def print_green(msg):
    msg_fmt = f"{colored(msg,'green')}"
    print ( msg_fmt )
    logger.get_logger("pricing_wizard",to_file=True).info( msg_fmt )

def print_green_bold(msg):
    msg_fmt = f"{colored(msg,'green',attrs=['bold'])}"
    print ( msg_fmt )
    logger.get_logger("pricing_wizard",to_file=True).info( msg_fmt )

def print_red(msg):
    msg_fmt = f"{colored(msg,'red')}"
    print ( msg_fmt )
    logger.get_logger("pricing_wizard",to_file=True).error( msg_fmt )

def print_red_bold(msg):
    msg_fmt = f"{colored(msg,'red',attrs=['bold'])}"
    print ( msg_fmt )
    logger.get_logger("pricing_wizard",to_file=True).error( msg_fmt )

def print_yellow(msg):
    msg_fmt = f"{colored(msg,'yellow')}"
    print ( msg_fmt )
    logger.get_logger("pricing_wizard",to_file=True).warning( msg_fmt )

def print_yellow_bold(msg):
    msg_fmt = f"{colored(msg,'yellow',attrs=['bold'])}"
    print ( msg_fmt )
    logger.get_logger("pricing_wizard",to_file=True).warning( msg_fmt )

def print_warning(msg):
    # Import the option handler in a limited use case to avoid circular reference
    from modules.options_handler import options_handler
    # Import the sqlite_logger in a limited use case to avoid circular reference
    from modules.sqlite_logger import sqlite_logger
    print_yellow_bold("PricingWizard : Warning")
    print_yellow_bold("-----------------------")
    print_yellow(msg)
    print_yellow_bold("-----------------------")
    __run_opts = options_handler()
    answer = __run_opts.yn_question("Acknowledge this warning and continue :")

    # sqlite logging for warnings
    s = sqlite_logger()
    s.add_warnings("test",answer,msg)

    if not answer:
        print_green_bold("Please investigate this warning.")
        raise KeyboardInterrupt

def tabulate_dataframe(df):
    print(colored(tabulate(df, headers='keys', tablefmt='psql'),'blue')+"\n\n") 

def print_exclaim_sameline(msg):
    msg_fmt = " - "+colored('!', 'green', attrs=['bold'])+" - "+colored(msg, 'blue', attrs=['bold'])
    print( msg_fmt, end='\r')

# Error handling utility

def exception_hook(exctype, value, tb):
    print("")
    if exctype == KeyboardInterrupt:
        print_green_bold(f"PricingWizard : Ending session! {value}\n")
        sys.exit(0)
    elif exctype == ValueError:
        print_red_bold("PricingWizard : ValueError")
        print_red_bold("--------------------------")
        print_red_bold(value.args[0]+"\n")
        # List of traceback
        if "invalid literal" in value.args[0]:
            err_details = traceback.format_tb(tb)
            for err_info in err_details:
                if 'pricing_wizard' in err_info:
                    print_red(" ---> "+err_info.strip())
        sys.exit(1)
    elif exctype == TypeError:
        print_red_bold("PricingWizard : TypeError")
        print_red_bold("-------------------------")
        print_red_bold(value.args[0]+"\n")
        # List of traceback
        # err_details = traceback.format_tb(tb)
        # print_red(" ---> "+err_details[-1].strip())
        sys.exit(2)
    elif exctype == NameError:
        # Usually indicates a coding problem (print stacktrace too)
        print_red_bold("PricingWizard : NameError")
        print_red_bold("-------------------------")
        print_red_bold(value.args[0]+"\n")
        err_details = traceback.format_tb(tb)
        print_red(" ---> "+err_details[-1].strip()+"\n")
        sys.exit(3)
    elif exctype == HttpError:
        print_red_bold("PricingWizard : HttpError from Google API")
        print_red_bold("-----------------------------------------")
        print_red_bold(value)
        print_green_bold("Please ensure that this spreadsheet is shared with 'Grover' in the share options.\n")
        sys.exit(4)
    elif exctype == InterfaceError:
        print_red_bold("PricingWizard : InterfaceError from RedShift")
        print_red_bold("--------------------------------------------")
        # Handle both connection timeout error and invalid username/password errors here
        try:
            print_red_bold (value.args[0]['M'])
            print_green_bold("Please ensure your username and password are valid.\n")
        except:
            print_red_bold(f"{' - '.join([str(x) for x in value.args])}")
            print_green_bold("Please ensure your Pritunl VPN is currently active to access RedShift database.\n")
        sys.exit(5)
    elif exctype == ProgrammingError:
        print_red_bold("PricingWizard : ProgrammingError from RedShift")
        print_red_bold("----------------------------------------------")
        try:
            print_red_bold (value.args[0]['M'])
            print_green_bold("Please check database access rights and configuration.\n")
        except:
            print_red_bold(f"{' - '.join([str(x) for x in value.args])}")
        sys.exit(5)

    else:
        sys.__excepthook__(exctype, value, tb)
