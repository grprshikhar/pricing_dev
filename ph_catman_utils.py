import pandas as pd
import os
import numpy as np
# import difflib
import re
import warnings

cat_dict = {'audio & music' : ['bluetooth speakers','dj equipment','headphones','hi-fi audio','musical instruments'],
	'cameras' : ['action cameras','camcorder','camera accessories','digital cameras','instant cameras','lenses','point-and-shoot'],
	'computers' : ['2-in-1 laptops','computing accessories','desktop computers','gaming computers','laptops','monitors'],
	'drones' : ['hobbyst & pro'],
	'emobility' : ['ebikes','gps & car accessories','hoverboards','scooters'],
	'gaming & vr' : ['gaming accessories','gaming consoles','retrogaming','virtual reality'],
	'home entertainment' : ['home cinema','projectors','tv < 49"','tv > 55"','tv 50" - 55"'],
	'phones & tablets' : ['phone accessories','smartphones','tablets'],
	'smart home' : ['intelligent security','light & electronics','robot cleaners','smart appliances'],
	'wearables' : ['activity trackers','apple watches','smartwatches','sport & gps trackers']
}

cat_list = list(cat_dict.keys())
sub_cat_list = [cat_dict[x] for x in cat_list]
sub_cat_list = [item for sublist in sub_cat_list for item in sublist]
df_cat_dict = pd.Series(cat_dict, name='subcategory').rename_axis('category').explode().reset_index()



store_dict = {'main_grover' : ['de','at','nl','es','us'],
	'b2b' : ['business','business_at','business_nl','business_es','business_us']}
store_parent_list = list(store_dict.keys())
store_code_list = [store_dict[x] for x in store_parent_list]
store_code_list = [item for sublist in store_code_list for item in sublist]

df_store_dict = pd.Series(store_dict, name='store code').rename_axis('store_parent').explode().reset_index()



df_cat_store_plans1 = df_cat_dict.copy()
df_cat_store_plans2 = df_cat_dict.copy()
df_cat_store_plans1["store_parent"] = "main_grover"
df_cat_store_plans2["store_parent"] = "b2b"

d_csp = df_cat_store_plans1.append(df_cat_store_plans2)
d_csp1 = d_csp.copy()
d_csp2 = d_csp.copy()
d_csp1["mp_critical"] = 1
d_csp2["mp_critical"] = 0
d_csp = d_csp2.append(d_csp1)

d_csp1 = d_csp.copy()
d_csp2 = d_csp.copy()
d_csp1["bulky"] = 1
d_csp2["bulky"] = 0
d_csp = d_csp2.append(d_csp1)

d_csp = d_csp.reset_index(drop=True)

d_csp["allowed_plans"]='(1,3,6,12,18,24)'

## 24 month plan rules

'hi-fi audio' > '18m'
'ebikes' > '18m'


### Removing all 24 M plans from B2C
d_csp.loc[ (d_csp["subcategory"]!='home appliances') & (d_csp["store_parent"]!='b2b') , "allowed_plans"] = '(1,3,6,12,18)'

### Removing all 24 M plans from B2B
d_csp.loc[ (~d_csp["subcategory"].isin(['home appliances','apple watches'])) & (d_csp["store_parent"]=='b2b')  & (~d_csp["category"].isin(['computers','phones & tablets'])), "allowed_plans"] = '(1,3,6,12,18)'

d_csp.loc[ (~d_csp["subcategory"].isin(['home appliances'])) & (d_csp["store_parent"]!='b2b')  & (~d_csp["category"].isin(['computers','home entertainment','fitness'])) & (d_csp["mp_critical"] == 0), "allowed_plans"] = '(1,3,6,12)'

d_csp.loc[ (d_csp["store_parent"]=='b2b')  & (d_csp["category"].isin(['computers'])), "allowed_plans"] = '(1,3,6,12,24)'

d_csp.loc[ (d_csp["category"].isin(['home entertainment','fitness'])) &  (~d_csp["subcategory"].isin(['projectors'])) , "allowed_plans"] = '(3,6,12,18)'
d_csp.loc[ (d_csp["subcategory"]=='home appliances'), "allowed_plans"] = '(6,12,18,24)'

def f():
	d_csp.loc[ (d_csp["bulky"]==1), "allowed_plans"] = d_csp.loc[ (d_csp["bulky"]==1), "allowed_plans"].str.replace(r'\(1,', '(')
	return d_csp

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    f()


d_csp= d_csp.merge(df_store_dict.drop_duplicates(), on=['store_parent'])




def store_loc(df):
	df['store code'] = df['store code'].str.lower()

	for store_id in ['de','at','nl','es','^us','business','b2b']:
		count_store = df['store code'].str.count(store_id)
		df_new = df.iloc[count_store[count_store>0].index].copy()
		df_new['store code']=store_id
		if store_id  in ['business','b2b'] :
			df_new['store code']='business'
		if store_id!='de':
			df_new2 = df_new2.append(pd.DataFrame(data = df_new), ignore_index=True)
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
	df_copy['comma_count_plan'] = df_copy.allowed_plans.str.count(',')
	df_copy = df_copy.drop(columns=[col for col in df_copy.columns if re.search(r'plan\d+', col)]).copy()
	df_out = pd.concat([df_copy.reset_index(drop=True), df_out.reset_index(drop=True)], axis=1)

	return df_out




