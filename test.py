

import os
import logging
# from sqlite import sqlite 	#our internal module, for local db interactions
# from utilities import logger_setup
# from selenium.webdriver.common.action_chains import ActionChains
import time
import random
from termcolor import colored,cprint
import sys



def restart_query():
    option_list = ['Wait. I think BO is still working.','Logout from BO. Restart this upload.','Exit Upload. I will do it manually!']

    confirm_selection='n'
    while confirm_selection=='n':

        first = random.choice(option_list)
        remaining = list(set(option_list)-set([first]))
        second = random.choice(remaining)
        last = list(set(remaining)-set([second]))[0]
        choice_dict = {
            1 : first,
            2 : second,
            3 : last
        }


        print("What do you want to do?\n1. "+choice_dict[1]+"\n2. "+choice_dict[2]+"\n3. "+choice_dict[3]+'\n')
        choice_response = input("Your Choice (1,2 or 3) : ")
        choice_response=str(choice_response)
        if choice_response not in ['1','2','3']:
           print("\nIncorrect response!\nPlease use only 1,2 or 3\n")
        else:
            print("\nYou entered: " + colored(choice_dict[int(choice_response)],'green')+"\n")
            confirm_selection = input("Is this correct (y/n/e) (e-exit program): ")
            confirm_selection=confirm_selection.lower()
        if confirm_selection not in ['y','n','e']:
            print(colored("Incorrect response!",'red'),"\n\nPlease use only (y/n/e) (e-exit program)\n")
            confirm_selection='n'
        elif confirm_selection=='e':
            print("\n\nYou selected not to exit program. Exiting now...\n\nPlease upload manually!\n\n")
            sys.exit()
        elif confirm_selection=='y' and choice_dict[int(choice_response)]=='Wait. I think BO is still working.':
            break

        elif confirm_selection=='y' and choice_dict[int(choice_response)]=='Logout from BO. Restart this upload.':
            print("\n\nDO THIS NOW\n\n")

        elif confirm_selection=='y' and choice_dict[int(choice_response)]=='Exit Upload. I will do it manually!':
            print("\n\nYou selected not to exit program. Exiting now...\n\nPlease upload manually!\n\n")
            sys.exit()


if __name__=="__main__":
	restart_query()

