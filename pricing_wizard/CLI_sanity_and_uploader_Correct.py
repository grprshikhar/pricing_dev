#!/usr/bin/env python

import pandas as pd
import os
import numpy as np
# import difflib
import re
import getpass
import sys
# import click
# import six
from tabulate import tabulate
# try:
#     import colorama
#     colorama.init(strip=not sys.stdout.isatty())
# except ImportError:
#     colorama = None

from termcolor import colored,cprint
from pyfiglet import figlet_format
import warnings
# import logging
# from sqlite import sqlite


cprint(figlet_format('\n',font='straight'),'white', 'on_grey', attrs=['bold']) 
cprint(figlet_format('Pricing\nWizard!\n',font='starwars',width = 200 ), 'red', attrs=['bold'])
cprint(figlet_format('\n',font='straight'),'white', 'on_grey', attrs=['bold'])

import ph_user_sheets as pus
import ph_catman_utils as phcu
import ph_gsheet_connect as pgc
path = r"/home/ubuntu/pricing_wizard"
os.chdir(path)
import ph_sanity_checks as psc
import ph_priceupload as ppu
import ph_gdrive_handler as phgdh
import logging
path = r"/home/ubuntu/pricing_wizard"
os.chdir(path)
import logger_setup
import getpass
from sqlite import sqlite 
from getpass import getpass




# logger_setup.logger_setup(logging.INFO, log_file="PMW_logs.log", rotating=True,
#     backup_count=2, max_bytes=10*1024*1024, sqlite_file=r"PMW_logs.db", sqlite_level=logging.INFO)
# logger = logging.getLogger('test')


# database = sqlite.connect(r'S:\internal\Scraping\output\Groundlink.db')
# cur = database.cursor()
# coords = cur.execute("select id from out_bid"+str(bid)+" group by 1;").fetchall()



user_name = pus.get_user()
export_dict=pus.export_dict
sheet_name = pus.get_sheet(user_name,export_dict)



# SPREADSHEET_ID = '1RXgSCkOFQt7pWMz2Qu_f3XtpU1kUkIPdIIi1gElk_3w'
# DATA_TO_PULL = 'Sheet1!A:M'
DATA_TO_PULL = 'Export!A:N'

try:
    data = pgc.pull_sheet_data(pgc.SCOPES,sheet_name,DATA_TO_PULL)
    df = pd.DataFrame(data)
    new_header = df.iloc[0]
    df = df[1:]
    df.columns = new_header
    df=df.reset_index(drop=True).copy()
    df.fillna("",inplace=True)
except FileNotFoundError:
    print('\n'+colored(sheet_name+' : No such file exists', 'red')+'\n')
    sys.exit()

df.columns = [x.lower() for x in df.columns]
df['category'] = df['category'].str.lower()
df['subcategory'] = df['subcategory'].str.lower()
df['bulky'] = df['bulky'].astype(int)
df['rrp'] = df['rrp'].astype(float)


#### Column type checks

psc.check_dataType(df)

print("\nNo Empty Cells - ",colored("Check",'green')+"\n")

psc.check_catnames(df)

print("Correct cat, sub-cat names - ",colored("Check",'green')+"\n")   

df_td = psc.clean_store_plan(df)

psc.check_discounts(df_td)

print("Discount values applied correctly - ",colored("Check",'green')+"\n")  

psc.check_plan_hierarchy(df_td)

print("Plan price hierarchy maintained - ",colored("Check",'green')+"\n") 

# logger.info("columns checked")

### Setting plan wise Hard boundaries
plan_limit_dict = {
    1 : [0.085,0.5],
    3 : [0.068,0.3],
    6 : [0.055,0.16],
    12 : [0.034,0.078],
    18 : [0.03,0.054],
    24 : [0.025,0.041]
}

psc.check_rrp_perc(df_td,plan_limit_dict)

print("RRP Percentage Guidelines - ",colored("Check",'green')+"\n\n")    

psc.last_digit_9 (df_td)

print("Decimal digit ends with 9 ",colored("Check",'green')+"\n\n")

df_td['new']= df_td['new'].fillna('')


#### Summarize data

see_upload=''
while see_upload=='':
    see_upload1 = input("View upload data summary (y/n): ")
    see_upload1=see_upload1.lower()
    if see_upload1 not in ['y','n']:
       print("\nIncorrect response!\nPlease use only 'y' or 'n'\n")
    elif see_upload1=='y':
        see_upload = see_upload1
        print("\n")
        psc.show_summary(df_td)
    else:
        see_upload = see_upload1
        print(colored("\n\nYou selected not to show the summary.\n\n",'yellow')) 



#### See Full Data

see_fulldata=''
while see_fulldata=='':
    see_fulldata1 = input("View Full Upload Data (y/n): ")
    see_fulldata1=see_fulldata1.lower()
    if see_fulldata1 not in ['y','n']:
       print("\nIncorrect response!\nPlease use only 'y' or 'n'\n")
    elif see_fulldata1=='y':
        see_fulldata = see_fulldata1
        disc_dt = df_td[['sku','store code','new','plan1','plan3','plan6','plan12','plan18','plan24']].copy()
        print(colored("Full upload data\n",'green')+colored(tabulate(disc_dt, headers='keys', tablefmt='psql'),'yellow')+"\n\n")   
    else:
        see_fulldata = see_fulldata1
        print(colored("\n\nYou selected not to show full data.\n\n",'yellow')) 




#### Upload data
prepare_upload=''
while prepare_upload=='':
    prepare_upload1 = input("Create upload file (yes/no): ")
    prepare_upload1=prepare_upload1.lower()
    if prepare_upload1 not in ['yes','no']:
       print("\nIncorrect response!\nPlease use only 'yes' or 'no'\n")
       prepare_upload1=''
    elif prepare_upload1=='no':
        prepare_upload=prepare_upload1
        print("\n\nYou selected not to create upload. Exiting now...\n\nNo new upload created!\n\n")
        sys.exit()
    else:
        prepare_upload=prepare_upload1

# Number of stores and entries

os.chdir("/home/ubuntu/Templates")


readTemplate_xls = 'template_stores.xlsx'

upload_sheet_map = pd.read_excel(readTemplate_xls, sheet_name=None)
sheet_names = list(upload_sheet_map.keys())
rental_plans = upload_sheet_map["rental_plans"]
column_ordered = rental_plans.columns.values
rental_plans[['SKU','Store code','Newness','1','3','6','12','18','24']] = df_td[['sku','store code','new','plan1','plan3','plan6','plan12','plan18','plan24']].copy()
rental_plans= rental_plans.fillna('')




confirm_fileOutxls='n'
while confirm_fileOutxls=='n':
    files_xls = input("What should be the upload file name ? :")
    fileout_name = files_xls+'.xlsx'
    print("\nYou entered: " + colored(fileout_name,'green')+"\n")
    confirm_fileOutxls = input("Is this correct (yes/no/exit) : ")
    confirm_fileOutxls=confirm_fileOutxls.lower()
    if confirm_fileOutxls not in ['yes','no','exit']:
        print(colored("Incorrect response!",'red'),"\n\nPlease use only (yes/no/exit)\n")
        confirm_fileOutxls='n'
    elif confirm_fileOutxls=='e':
        print("\n\nYou selected not to create upload. Exiting now...\n\nNo new upload created!\n\n")
        sys.exit()


## Create a Pandas Excel writer using XlsxWriter as the engine.

os.chdir("/home/ubuntu/upload_files")

with pd.ExcelWriter(fileout_name) as writer:
    rental_plans.to_excel(writer, sheet_name="rental_plans",index=False)
#def reader():
#    writer = pd.ExcelWriter(fileout_name, engine='xlwt')
#    return writer

#with warnings.catch_warnings():
#    warnings.simplefilter("ignore")
#    writer = reader()


## Write each dataframe to a different worksheet.
#sheet_names.remove('rental_plans')

#for sheets in sheet_names:
#    df = upload_sheet_map[sheets]
#    df.to_excel(writer, sheet_name=sheets, index=False)

#rental_plans.to_excel(writer, sheet_name='rental_plans', index=False)



## Close the Pandas Excel writer and output the Excel file.
#writer.save()

# os.chdir(r'/Users/shikharsrivastava/Google Drive/My Drive/Dev/Pricing_automation/pricing_wizard')
body = {'name': fileout_name, 'parents':[phgdh.folder_id],'mimeType': phgdh.mime_type}
media = phgdh.MediaFileUpload(fileout_name, mimetype = phgdh.mime_type)
fiahl = phgdh.service.files().create(body=body, media_body=media).execute()


print("\n\n")
cprint("   ~~~$~~~    Upload File: "+fiahl.get('name')+" Created    ~~~$~~~    ",'white','on_blue', attrs=['bold','underline'])
print("\n\nFile location : Google Drive/Pricing/Price Uploads/Price Upload - Sanity Checked/\n\n")



file_location_local = r"/home/ubuntu/upload_files/"+fileout_name
confirm_BO_Upload='n'
chrome_path=r'/home/ubuntu/pricing_wizard/chromedriver'
while confirm_BO_Upload=='n':
    confirm_BO_Upload = input("Want to upload the file to BO directly? (yes/exit): ")
    # confirm_BO_Upload = input("Really want to upload? (yes/exit): ")
    confirm_BO_Upload=confirm_BO_Upload.lower()
    if confirm_BO_Upload not in ['yes','exit']:
        print(colored("Incorrect response!",'red'),"\n\nPlease use only 'yes' or 'exit'\n")
        confirm_BO_Upload='n'
    elif confirm_BO_Upload=='exit':
        print("\n\nYou selected not to upload. Exiting now...\n\nYou can upload manually !\n\n")
        sys.exit()
    else:
        bo_login_id = input("BO Login Name:")
        bo_login_pwd = getpass()
        ppu.bo_upload(file_location_local,chrome_path,bo_login_id,bo_login_pwd)


print("\n\n")

cprint("   ~~~$~~~ Prices are uploaded at Backoffice  ~~~$~~~    ",'white','on_blue', attrs=['bold','underline'])

print("\n\n")

