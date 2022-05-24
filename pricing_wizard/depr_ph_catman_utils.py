import pandas as pd
import os
import numpy as np
# import difflib
import re
import warnings

import ph_gsheet_connect as pgc

try:
    sheet_name_rp = '1VhyEO0BRVXp3mJ9abXJ0EYiF34Fhu50qv6m9nuldIPI'
    DATA_TO_PULL_rp = 'CSV Export!A:K'
    data_rp = pgc.pull_sheet_data(pgc.SCOPES,sheet_name_rp,DATA_TO_PULL_rp)
    df_rp = pd.DataFrame(data_rp)
    new_header2 = df_rp.iloc[0]
    df_rp = df_rp[1:]
    df_rp.columns = new_header2
    df_rp=df_rp.reset_index(drop=True).copy()
    df_rp.fillna("",inplace=True)
except FileNotFoundError:
    print('\n'+colored(sheet_name+' : No such file exists', 'red')+'\n')
    print('\n'+colored('Please check that Rental Durations sheet is working ^^', 'red')+'\n')
    sys.exit()

df_rp['bulky'] = df_rp['bulky'].astype(int)

df_cat_dict = df_rp[["category", "subcategory"]].drop_duplicates()
cat_list = df_rp["category"].unique().tolist()
cat_list = [x.lower() for x in cat_list]
sub_cat_list =  df_rp["subcategory"].unique().tolist()
sub_cat_list = [x.lower() for x in sub_cat_list]


store_dict = {'de' : ['de','at','nl','es'],
	'us' : ['us'],
	'business' : ['business','business_at','business_nl','business_es']}
duration_plan_leader_list = list(store_dict.keys())
store_code_list = [store_dict[x] for x in duration_plan_leader_list]
store_code_list = [item for sublist in store_code_list for item in sublist]

df_store_dict = pd.Series(store_dict, name='store code').rename_axis('duration_plan_leader').explode().reset_index()



d_csp = df_rp.merge(df_store_dict.drop_duplicates(), on=['duration_plan_leader'])
d_csp['bulky'] = d_csp['bulky'].astype(int)


d_csp = d_csp.apply(lambda x: x.astype(str).str.lower())

def store_loc(df):
	df['store code'] = df['store code'].str.lower()

	for store_id in ['de','at','nl','es','^us','business','b2b']:
		count_store = df['store code'].str.count(store_id)
		df_new = df.iloc[count_store[count_store>0].index].copy()
		df_new['store code']=store_id
		if store_id  in ['business','b2b'] :
			df_new['store code']='business'
		if store_id!='de':
			df_new2 = pd.concat([df_new2,pd.DataFrame(data = df_new)], ignore_index=True)
		else:
			df_new2 = df_new.copy()
	return 	df_new2	


def price_loc(df):
	df_copy = df.copy()
	df_plans = df.filter(regex=r'plan\d+')
	df_plans_out = pd.concat([df_plans.reset_index(drop=True), df_plans.add_prefix("active_")], axis=1)
	df_plans_out = pd.concat([df_plans_out.reset_index(drop=True), df_plans.add_prefix("high_")], axis=1)
	rrp = df_copy.rrp
	for subplan in [1,3,6,12,18,24]:
		df_subplanwise = df_plans_out.filter(regex=str(subplan)+"$")
		df_subplanwise = df_subplanwise.applymap(str)
		to_allot = df_subplanwise[('plan'+str(subplan))].str.split(',', 1, expand=True)
		if issubclass(type(to_allot), pd.core.frame.DataFrame) and to_allot.shape[1]!=1:
			df_subplanwise['active_plan'+str(subplan)], df_subplanwise['high_plan'+str(subplan)] = pd.to_numeric(to_allot[0],errors='coerce'),pd.to_numeric(to_allot[1],errors='coerce')
		else :
			df_subplanwise['active_plan'+str(subplan)],	df_subplanwise['high_plan'+str(subplan)] = pd.to_numeric(to_allot[0],errors='coerce'),pd.to_numeric(to_allot[0],errors='coerce')

		df_subplanwise[('act_perc_pp_'+str(subplan))] = df_subplanwise['active_plan'+str(subplan)]/rrp
		df_subplanwise[('high_perc_pp_'+str(subplan))] = df_subplanwise['high_plan'+str(subplan)]/rrp
		df_subplanwise[('disc_perc_'+str(subplan))] = (df_subplanwise['high_plan'+str(subplan)]-df_subplanwise['active_plan'+str(subplan)])/df_subplanwise['high_plan'+str(subplan)]
		if subplan==1:
			df_out = df_subplanwise
		else:	
			df_out = pd.concat([df_out.reset_index(drop=True), df_subplanwise.reset_index(drop=True)], axis=1)

	df_copy['check'] = pd.Series(df_copy[[col for col in df_copy.columns if re.search(r'plan\d+', col)]].fillna('').values.tolist()).str.join('')
	df_copy['check']= df_copy['check'].fillna('')
	df_copy['comma_count'] = df_copy.check.str.count(',')
	df_copy['comma_count_plan'] = df_copy.duration_plan.str.count(',')
	df_copy = df_copy.drop(columns=[col for col in df_copy.columns if re.search(r'plan\d+', col)]).copy()
	df_out = pd.concat([df_copy.reset_index(drop=True), df_out.reset_index(drop=True)], axis=1)

	return df_out




