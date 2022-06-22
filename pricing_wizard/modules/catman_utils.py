import re
import modules.gsheet as gsheet
import pandas as pd
import sys

class catman_utils(object):
	def __init__(self):
		# Rental plan sheet
		self.sheet_id = '1VhyEO0BRVXp3mJ9abXJ0EYiF34Fhu50qv6m9nuldIPI'
		self.data_range = 'CSV Export!A:K'
		self.df = gsheet.get_dataframe(self.sheet_id, self.data_range, "Market rental plans")
		self.sanitise()

	def sanitise(self):
		# Ensure type - int
		self.df['bulky']  = self.df['bulky'].astype(int)
		# Generate dictionary : category - subcategory
		self.cat_dict     = self.df[["category", "subcategory"]].drop_duplicates()
		# Generate list of unique categories
		cat_list          = self.df["category"].unique().tolist()
		self.cat_list     = [x.lower() for x in cat_list]
		# Generate list of unique subcategories
		sub_cat_list      = self.df["subcategory"].unique().tolist()
		self.sub_cat_list = [x.lower() for x in sub_cat_list]
		# Manage store name/types
		self.store_dict   = {'de' : ['de','at','nl','es'],
							 'us' : ['us'],
							 'business' : ['business','business_at','business_nl','business_es']}
		duration_plan_leader_list = list(self.store_dict.keys())
		store_code_list = [self.store_dict[x] for x in duration_plan_leader_list]
		self.store_code_list = [item for sublist in store_code_list for item in sublist]
		self.df_store_dict = pd.Series(self.store_dict, name='store code').rename_axis('duration_plan_leader').explode().reset_index()
		# Merge the rental plan sheets with the stores in which they are permitted
		# df_csp = datafram category subcategory plan
		self.df_csp          = self.df.merge(self.df_store_dict.drop_duplicates(), on=['duration_plan_leader'])
		# This apply will overwrite and set everything to string
		self.df_csp          = self.df_csp.apply(lambda x: x.astype(str).str.lower())
		# So need to reset bulky to integer
		self.df_csp['bulky'] = self.df_csp['bulky'].astype(int)

	def info(self):
		print ("Information from catman utils")
		print (self.cat_dict)
		print (self.cat_list)
		print (self.sub_cat_list)
		print (self.store_code_list)
		print (self.store_dict)
		print (self.df_store_dict)
		print (self.df_csp)


	def store_loc(self, df):
		# Clean column
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


	def price_loc(self, df):
		df_copy  = df.copy()
		df_plans = df.filter(regex=r'^plan\d+')
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

		df_copy['check'] = pd.Series(df_copy[[col for col in df_copy.columns if re.search(r'^plan\d+', col)]].fillna('').values.tolist()).str.join('')
		df_copy['check'] = df_copy['check'].fillna('')
		df_copy['comma_count'] = df_copy.check.str.count(',')
		df_copy['comma_count_plan'] = df_copy.duration_plan.str.count(',')
		df_copy = df_copy.drop(columns=[col for col in df_copy.columns if re.search(r'^plan\d+', col)]).copy()
		df_out = pd.concat([df_copy.reset_index(drop=True), df_out.reset_index(drop=True)], axis=1)

		# Convert type for the old price columns for use later in EU checks
		for rp in [1,3,6,12,18,24]:
			df_out[f"old_low_plan{rp}"] = pd.to_numeric(df_out[f"old_low_plan{rp}"], errors='coerce')
			df_out[f"old_high_plan{rp}"] = pd.to_numeric(df_out[f"old_high_plan{rp}"], errors='coerce')

		return df_out

	# Checks category names against catman data, so merge functionality
	def check_catnames(self, df):
		if (~df['category'].isin(self.cat_list).values).any():
			out_error = "Incorrect category values: "+str((df[~df['category'].isin(self.cat_list)]['category'].values))
			raise ValueError(out_error)

		if (~df['subcategory'].isin(self.sub_cat_list).values).any():
			out_error = "Incorrect Subcategory values: "+str((df[~df['subcategory'].isin(self.sub_cat_list)]['subcategory'].values))
			raise ValueError(out_error)

	# Cleaning the store plan
	def clean_store_plan(self, df):
		df_init = self.store_loc(df)

		if (~df_init['store code'].isin(self.store_code_list).values).any():
			out_error = "Incorrect store code values: "+str((df_init[~df_init['store code'].isin(self.store_code_list)]['store code'].values))
			raise ValueError(out_error)

		df_init = df_init.merge(self.df_csp.drop_duplicates(), on=['category','subcategory','store code','bulky'])

		df_td = self.price_loc(df_init)

    	#### Plan curation
    	## if plan allowed is there but not in plan price > Raise error
		for subplan in [1,3,6,12,18,24]:
			act_price_col = 'active_plan'+str(subplan)
			regex = str(subplan)+r',|'+str(subplan)+r'\)'
			sku_list = df_td.loc[(df_td[act_price_col].isnull()) & (df_td['duration_plan'].str.contains(regex)),['sku','store code']]
			if len(sku_list)>0:
				raise ValueError('Missing %d Month price plans for SKUs : '%subplan + str(sku_list) )

    	## if plan price is there but not in plan allowed > Remove plan price
		for subplan in [1,3,6,12,18,24]:
			act_price_col = 'active_plan'+str(subplan)
			plan_tochange = 'plan'+str(subplan)
			regex         = str(subplan)+r',|'+str(subplan)+r'\)'
			df_td.loc[(~df_td[act_price_col].isnull()) & (~df_td['duration_plan'].str.contains(regex)),plan_tochange] = ''

		df_init = df_td[df_init.columns.values].copy()
		df_td   = self.price_loc(df_init)
		return df_td





