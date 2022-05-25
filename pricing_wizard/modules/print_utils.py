import sys
import traceback
from termcolor import colored
from googleapiclient.errors import HttpError

# Print utility
def print_check(msg):
    print(" - "+colored(u'\u2713', 'green', attrs=['bold'])+" - "+msg)

def print_green(msg):
    print (f"{colored(msg,'green')}")

def print_green_bold(msg):
    print (f"{colored(msg,'green',attrs=['bold'])}")

def print_red(msg):
    print (f"{colored(msg,'red')}")

def print_red_bold(msg):
    print (f"{colored(msg,'red',attrs=['bold'])}")


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
        # err_details = traceback.format_tb(tb)
        # print_red(" ---> "+err_details[-1].strip())
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
    else:
        sys.__excepthook__(exctype, value, tb)
