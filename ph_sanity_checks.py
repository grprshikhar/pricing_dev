#!/usr/bin/env python

import pandas as pd
import numpy as np
import re
import sys
from tabulate import tabulate
try:
    import colorama
    colorama.init(strip=not sys.stdout.isatty())
except ImportError:
    colorama = None
from termcolor import colored,cprint
from pyfiglet import figlet_format
import warnings
import ph_catman_utils as phcu
# from ph_catman_utils import *

def check_dataType(df):
    if df.sku.isnull().values.any() or (~df.sku.str.contains('GR').values).any():
        try:
            raise ValueError("\nSKU column has empty values\n\n")
        except ValueError as v:
            print(v.args[0])
            sys.exit()

    if df.category.isnull().values.any():
        try:
            raise ValueError("\nCategory column has empty values\n\n")
        except ValueError as v:
            print(v.args[0])
            sys.exit()


    if df.subcategory.isnull().values.any():
        try:
            raise ValueError("\nSubcategory column has empty values\n\n")
        except ValueError as v:
            print(v.args[0])
            sys.exit()


    if df.bulky.isnull().values.any():
        try:
            raise ValueError("\nBulky column has empty values\n\n")
        except ValueError as v:
            print(v.args[0])
            sys.exit()


    if not isinstance(df.sku.values[0],str): 
        try:
            raise TypeError("\nSKUs are not string data type! Check input file again.\n\n")
        except TypeError as v:
            print(v.args[0])
            sys.exit()


    if not isinstance(df.category.values[0],str): 
        try:
            raise TypeError("\nCategories are not string data type! Check input file again.\n\n")
        except TypeError as v:
            print(v.args[0])
            sys.exit()

    if not isinstance(df.subcategory.values[0],str): 
        try:
            raise TypeError("\nCategories are not string data type! Check input file again.\n\n")
        except TypeError as v:
            print(v.args[0])
            sys.exit()

    if isinstance(df.bulky.values[0],str) or (~df.bulky.isin([0,1]).values).any():
        try:
            raise TypeError("\nBulky column has incorrect values! Check input file again.\n\n")
        except TypeError as v:
            print(v.args[0])
            sys.exit()

    if isinstance(df.rrp.values[0],str) or (df.rrp==0).values.any() or df.rrp.isnull().values.any(): 
        try:
            raise TypeError("\nRRP is not correctly filled! Check input file again.\n")
        except TypeError as v:
            print(v.args[0])
            sys.exit()
    
    



#### Cat and sub-cat name and combination checks
def check_catnames(df):
    if (~df['category'].isin(phcu.cat_list).values).any():
        out_error = "Incorrect category values: "+str((df[~df['category'].isin(phcu.cat_list)]['category'].values))
        try:
            raise ValueError("\n"+out_error+"\n\n")
        except ValueError as v:
            print(v.args[0])
            sys.exit()


    if (~df['subcategory'].isin(phcu.sub_cat_list).values).any():
        out_error = "Incorrect Subcategory values: "+str((df[~df['subcategory'].isin(phcu.sub_cat_list)]['subcategory'].values))
        try:
            raise ValueError("\n"+out_error+"\n\n")
        except ValueError as v:
            print(v.args[0])
            sys.exit()


    check_cat_subcat_map = df.merge(phcu.df_cat_dict.drop_duplicates(), on=['category','subcategory'], 
                       how='left', indicator=True)

    if (check_cat_subcat_map['_merge'] == 'left_only').any():
        dt_err = check_cat_subcat_map[check_cat_subcat_map['_merge'] == 'left_only']
        dt_err['combined'] = dt_err[['category','subcategory']].apply(lambda row: ' <> '.join(row.values.astype(str)), axis=1)
        out_error = "Incorrect Category & Subcategory match: "+dt_err['combined'].values
        try:
            raise ValueError("\n"+out_error+"\n\n")
        except ValueError as v:
            print(v.args[0])
            sys.exit()
    
    # return print("\nCorrect cat, sub-cat names  - ",colored("Check",'green')+"\n")    





#### Cat and sub-cat name and combination checks

def clean_store_plan(df):
    df_init = phcu.store_loc(df)

    mp_critical = 2000
    df_init['mp_critical'] = 0
    df_init.loc[ (df_init["rrp"]>=mp_critical), "mp_critical"] = 1

    if (~df_init['store code'].isin(phcu.store_code_list).values).any():
        out_error = "Incorrect store code values: "+str((df_init[~df_init['store code'].isin(phcu.store_code_list)]['store code'].values))
        try:
            raise ValueError("\n"+out_error+"\n\n")
        except ValueError as v:
            print(v.args[0])
            sys.exit()


    df_init = df_init.merge(phcu.d_csp.drop_duplicates(), on=['category','subcategory','store code','mp_critical','bulky'])


    df_td = phcu.price_loc(df_init)

    #### Plan curation

    ## if plan allowd is there but not in plan price > Raise error
    for subplan in [1,3,6,12,18,24]:
        act_price_col = 'active_plan'+str(subplan)
        regex = str(subplan)+r',|'+str(subplan)+r'\)'
        sku_list = df_td.loc[(df_td[act_price_col].isnull()) & (df_td['allowed_plans'].str.contains(regex)),['sku','store code']]
        if len(sku_list)>0:
            # print('Missing %d Month price plans for SKUs :\n\n' % subplan,sku_list)
            try:
                raise ValueError("\n"+'Missing %d Month price plans for SKUs : \n'%subplan +str(sku_list)+"\n\n")
            except ValueError as v:
                print(v.args[0])
                sys.exit()

    ## if plan price is there but not in plan allowed > Remove plan price
     
    for subplan in [1,3,6,12,18,24]:
        act_price_col = 'active_plan'+str(subplan)
        plan_tochange = 'plan'+str(subplan)
        regex = str(subplan)+r',|'+str(subplan)+r'\)'
        df_td.loc[(~df_td[act_price_col].isnull()) & (~df_td['allowed_plans'].str.contains(regex)),plan_tochange]=''

    df_init = df_td[df_init.columns.values].copy()
    df_td = phcu.price_loc(df_init)

    return df_td





# If discount is present then check if it's for all plans or not
def check_discounts(df_td):
    if df_td[(df_td.comma_count!=df_td.comma_count_plan+1) & (df_td.comma_count>0)].values.any():
        SKU = df_td.loc[(df_td.comma_count!=df_td.comma_count_plan+1),'sku']
        # print('Inconsistent discounts for SKUs :\n\n',sku_list)
        try:
            raise ValueError("\n"+"Discount is missing for \n"+str(SKU.values)+"\n\n")
        except ValueError as v:
            print(v.args[0])
            sys.exit()
  




def check_plan_hierarchy(df_td):
    # Longer plan active values can't be more expensive than shorter
    list_plans = [1,3,6,12,18,24]
    i=0
    for plan in [3,6,12,18,24]:
        ag = list_plans[i]
        i+=1
        pc = "plan"+str(plan)
        agnst = "plan"+str(ag)
        pc_act = "active_plan"+str(plan)
        agnst_act = "active_plan"+str(ag)   
        
        if df_td.loc[(df_td[agnst]!='') & (df_td[pc]!='') & (df_td[agnst_act]<=df_td[pc_act])].empty!=True:
            sku = df_td.loc[(df_td[agnst_act]<=df_td[pc_act]),'sku']
            try:
                raise ValueError("\n"+str(plan)+"M Plan Price is Expensive than \n"+str(ag)+"M for "+str(sku.values)+"\n\n")
            except ValueError as v:
                print(v.args[0])
                sys.exit()


    # Longer plan high values can't be more expensive than shorter
    i=0
    for plan in [3,6,12,18,24]:
        ag = list_plans[i]
        i+=1
        pc = "plan"+str(plan)
        agnst = "plan"+str(ag)
        pc_act = "high_plan"+str(plan)
        agnst_act = "high_plan"+str(ag) 
        
        if df_td.loc[(df_td[agnst].str.contains(',')) & (df_td[agnst_act]<=df_td[pc_act])].empty!=True:
            sku = df_td.loc[(df_td[agnst_act]<=df_td[pc_act]),'sku']
            try:
                raise ValueError("\n"+str(plan)+"M Plan High Price is Expensive than \n"+str(ag)+"M for "+str(sku.values)+"\n\n")
            except ValueError as v:
                print(v.args[0])
                sys.exit()

    return print("Plan price hierarchy maintained - ",colored("Check",'green')+"\n")    



### Setting plan wise Hard boundaries in %RRP

'''
CREATE A PLAN BOUNDARY DICTIONARY LIKE:
plan_limit_dict = {
    1 : [0.085,0.5],
    3 : [0.068,0.3],
    6 : [0.055,0.16],
    12 : [0.034,0.078],
    18 : [0.03,0.054],
    24 : [0.025,0.041]
}
'''

def check_rrp_perc(df_td,plan_limit_dict):
    for k, dk in plan_limit_dict.items():
        act_pp = "act_perc_pp_"+str(k)
        low_limit = dk[0] 
        high_limit = dk[1]
        if df_td.loc[(df_td[act_pp]<=low_limit)].empty!=True:
            sku = df_td.loc[(df_td[act_pp]<=low_limit),'sku']
            try:
                raise ValueError("\n"+str(k)+"M Plan Price is too cheap for SKUs : \n"+str(sku.values)+"\n\n")
            except ValueError as v:
                print(v.args[0])
                sys.exit()
        
        if df_td.loc[(df_td[act_pp]>=high_limit)].empty!=True:
            sku = f_td.loc[(df_td[act_pp]>=high_limit),'sku']
            try:
                raise ValueError("\n"+str(k)+"M Plan Price is too expensive for SKUs : \n"+str(sku.values)+"\n\n")
            except ValueError as v:
                print(v.args[0])
                sys.exit()

    return print("RRP Percentage Guidelines - ",colored("Check",'green')+"\n\n")    


def last_digit_9 (df_td):
    for plan in [1,3,6,12,18,24]:
        pc = "active_plan"+str(plan)
        if df_td.loc[(df_td[pc]*10%10<9) | (df_td[pc]*10%10>9)].empty!=True:
            sku = df_td.loc[(df_td[pc]*10%10<9) & (df_td[pc]*10%10>9),'sku']
            try:
                raise ValueError("\n"+str(plan)+"M Plan has non Charm prices for SKUs : \n"+str(sku.values)+"\n\n")
            except ValueError as v:
                print(v.args[0])
                sys.exit()
   


#### Summarize data

def show_summary(df_td):
        desc_prices = df_td.describe(exclude=['object','int'])
        print("\n")
        cprint("$$  Total Price Uploads - "+str(len(df_td))+"  $$",'white','on_blue', attrs=['bold','blink'])
        print(colored("\n\n>>## Total Bulky Items - ",'green'),colored(str(sum(df_td.bulky)),'yellow')+"\n")  
        print(colored(">>$$ Total RRP > 2000 Items - ",'green'),colored(str((df_td.rrp>2000).count()),'yellow')+"\n\n")  
        a=df_td['allowed_plans'].value_counts().rename_axis('Plans').reset_index(name='Price uploads')
        print(colored("Number of uploads per plan\n",'green')+colored(tabulate(a, headers='keys', tablefmt='psql'),'yellow')+"\n")

        a=df_td['store code'].value_counts().rename_axis('Store Codes').reset_index(name='Price uploads')
        print(colored("Number of uploads for each store\n",'green')+colored(tabulate(a, headers='keys', tablefmt='psql'),'yellow')+"\n")

        a=df_td['subcategory'].value_counts().rename_axis('Subcategory').reset_index(name='Price uploads')
        print(colored("Number of uploads for each Subcategory\n",'green')+colored(tabulate(a, headers='keys', tablefmt='psql'),'yellow')+"\n")

        pp_dt = desc_prices[[col for col in desc_prices.columns if 'act_perc_pp' in col]]
        pp_dt.columns = pp_dt.columns.str.replace("act_perc_pp_", "Act PP % ")
        print(colored("New Active PP Percentage data summary\n",'green')+colored(tabulate(pp_dt, headers='keys', tablefmt='psql'),'yellow')+"\n")
        acti_dt = desc_prices[[col for col in desc_prices.columns if 'acti' in col]]
        acti_dt.columns = acti_dt.columns.str.replace("active_plan", "Active Plan ")
        print(colored("New Active Price data summary\n",'green')+colored(tabulate(acti_dt, headers='keys', tablefmt='psql'),'yellow')+"\n")
        high_dt = desc_prices[[col for col in desc_prices.columns if 'high_plan' in col]]
        high_dt.columns = high_dt.columns.str.replace("high_plan", "High Plan ")
        print(colored("New High Price data summary\n",'green')+colored(tabulate(high_dt, headers='keys', tablefmt='psql'),'yellow')+"\n")    
        disc_dt = desc_prices[[col for col in desc_prices.columns if 'disc' in col]]
        print(colored("Discount data summary\n",'green')+colored(tabulate(disc_dt, headers='keys', tablefmt='psql'),'yellow')+"\n\n")   



