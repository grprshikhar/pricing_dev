'''
name: ph_priceupload.py
function: uploads prices to BackOffice with Selenium
created on: 2022-01-15
created by: shikhar
'''


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException ### for new wait for element functions
import selenium.webdriver.support.ui as ui
from selenium import webdriver
import os
import logging
# from sqlite import sqlite 	#our internal module, for local db interactions
# from utilities import logger_setup
# from selenium.webdriver.common.action_chains import ActionChains
import time
import random
from termcolor import colored,cprint
import sys
# import user_utils
import re

# return True if element is visible within 2 seconds, otherwise False
def is_visible(driver,locator, timeout):
    try:
        ui.WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((By.XPATH, locator)))
        return True
    except TimeoutException:
        return False



def bo_upload(file_location,path,bo_login_id,bo_login_pwd):
    options = webdriver.ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(path, options=options)
    time.sleep(2)
    driver.get("https://backoffice.getgrover.com/users/sign_in")
    time.sleep(5)

    if is_visible(driver,"//*[@id='user_email']",timeout=20) == True: username = driver.find_element_by_id("user_email")
    else: raise RuntimeError('Could not find text box for email_id')

    if is_visible(driver,"//*[@id='user_password']",timeout=20) == True: password = driver.find_element_by_id("user_password")
    else: raise RuntimeError('Could not find text box for password')

    username.send_keys(bo_login_id)
    password.send_keys(bo_login_pwd)


    if is_visible(driver,"//*[@name='commit']",timeout=20) == True: driver.find_element_by_name("commit").click()
    else: raise RuntimeError('Could not login after email and password entry')

    print("BackOffice login - ",colored("Done",'green')+"\n\n")    


    time.sleep(5)
    driver.get("https://backoffice.getgrover.com/operations/upload/new")

    input_file = file_location

    if is_visible(driver,"//*[@id='upload_sheet']",timeout=20) == True: driver.find_element_by_xpath("//*[@id='upload_sheet']").send_keys(input_file)
    else: raise RuntimeError('could not find the find sheet button')

    print("Sheet attached - ",colored("Done",'green')+"\n\n")    


    if is_visible(driver,"//*[@name='commit']",timeout=10) == True: driver.find_element_by_xpath("//*[@name='commit']").click()
    else: raise RuntimeError('could not find the upload sheet button')

    print("Upload button clicked - ",colored("Done",'green')+"\n\n")    

    print(colored("Uploading...",'blue')+"\n\n")    

    if is_visible(driver,"//*[@class='ibox']",timeout=60) == True: text_list = driver.find_elements_by_xpath("//div[@class='ibox']")
    else: raise RuntimeError('could not upload the sheet')


### Discuss with Marco

    # min_counter_1=0
    min_counter_2=0
    min_counter_5=0
    min_counter_10=0
    perc_done_new=0
    perc_done_old=0
    start = time.time()
    while '100' not in text_list[2].text :
        perc_done_new = int(re.findall(r'\d+', text_list[2].text)[0])
        if perc_done_old==perc_done_new:
            if round(time.time()-start)>120 & round(time.time()-start)<300 and min_counter_2==0:
                min_counter_2+=1
                print("\nUploading is stuck and it's been more than two minutes !!\n")
                restart_query(file_location)
            if round(time.time()-start)>300 & round(time.time()-start)<600 and min_counter_5==0:
                min_counter_5+=1
                print("\nUploading is stuck and it's been more than 5 minutes!!\n")    
                restart_query(file_location)        
            if round(time.time()-start)>300 & round(time.time()-start)<600 and min_counter_5==0:
                min_counter_10+=1
                print("\nUploading is stuck and it's been more than 10 minutes!!\n")    
                restart_query(file_location)       
                print("\nOkay I will not ask this again, use ctrl+c to end this program!\n")    
       
        else:
            start = time.time()
            perc_done_old = perc_done_new          
            if perc_done_new%10!=0 : 
                continue
            else:
                print('\n'+str(perc_done_new)+'% done')    

  
    time.sleep(10)

    print(text_list[2].text)
    print(text_list[3].text)
    driver.quit()



def restart_query(file_location):
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
            driver.quit()
            sys.exit()
        elif confirm_selection=='y' and choice_dict[int(choice_response)]=='Wait. I think BO is still working.':
            break

        elif confirm_selection=='y' and choice_dict[int(choice_response)]=='Logout from BO. Restart this upload.':
            driver.quit()
            print("\n\nRestarting BO Sign In\n\n")
            bo_upload(file_location)

        elif confirm_selection=='y' and choice_dict[int(choice_response)]=='Exit Upload. I will do it manually!':
            print("\n\nYou selected not to exit program. Exiting now...\n\nPlease upload manually!\n\n")
            driver.quit()
            sys.exit()
