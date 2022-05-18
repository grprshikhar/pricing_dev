#!/usr/bin/env python


import re
import sys
from tabulate import tabulate

from termcolor import colored,cprint
from pyfiglet import figlet_format
import warnings


def valerror_exit(out_comment):
    try:
        raise ValueError("\n+out_comment+\n\n")
    except ValueError as v:
        print(colored(v.args[0],'red'))
        sys.exit()

def typeerror_exit(out_comment):
    try:
        raise TypeError("\n+out_comment+\n\n")
    except TypeError as v:
        print(colored(v.args[0],'red'))
        sys.exit()

def print_check(check_comment):
    print("\n"+check_comment+" - ",colored("Check",'green')+"\n")


def choice_selection(query):

    to_do ='n'
    while to_do=='n':
        question_upload = input("Want to upload the file to BO directly? (y/e) (e-exit program):")
        confirm_BO_Upload = input("Is this correct (y/e) (e-exit program): ")
        confirm_BO_Upload=confirm_BO_Upload.lower()
        if question_upload not in ['y','e']:
            print(colored("Incorrect response!",'red'),"\n\nPlease use only 'y' or 'n'\n")
            confirm_BO_Upload='n'
        elif confirm_BO_Upload=='e':
            print("\n\nYou selected not to create upload. Exiting now...\n\nNo new upload created!\n\n")
            sys.exit()
        else:
            ppu.bo_upload(file_location)
