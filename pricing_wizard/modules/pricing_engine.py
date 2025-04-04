import pandas
import numpy as np
import modules.gsheet as gsheet
import modules.gdrive as gdrive
from modules.warning_tracker import warning_tracker, warning_object
from modules.sku_data import sku_data
from modules.print_utils import print_exclaim, print_check
import datetime

class pricing_engine(object):
	def __init__(self, run_opts):
		self.run_opts         = run_opts
		self.sheet_range      = f"{run_opts.get_user()}!A4:B"
		self.engine_filter    = gsheet.get_dataframe(self.run_opts.current_sheet, self.sheet_range, f"Pricing engine hightouch sheet with tab name {run_opts.get_user()}")
		self.engine_dataframe = gsheet.get_dataframe(self.run_opts.current_sheet, 'optimiser_prices!B:N', f"Pricing engine prices")
		self.df               = None
		self.df_stores        = None
		self.get_store_codes()
		self.get_rrp()
		self.apply_user_filtering()
		self.generate_upload_format()


	def get_store_codes(self):
		# We need to include the store information
		sheet_id       = '153fzJOWK7HFnNil_LMd6sLz1kOFz4ZVBxy-etsCnIGA'
		data_range     = 'redshift_export!A:B'
		self.df_stores = gsheet.get_dataframe(sheet_id, data_range,"Store parent list")

	def get_rrp(self):
		# We need to include our rrp information
		scraper_mkt          = ('1QB_50NBuVlvlz3Y37SrAD7HHVXfx2GxyHFq4iqIX7xQ', "Sheet1!A:T","Scraper market prices")
		mm_mkt               = ('1IQIPm3R18mDn9iGJKJLoqTGEecgjKAqfmFaRo-9OfaY',"MM Feed!H:O","MM market prices")
		bo_rrp               = ('1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew',"Financial!A:E","BO rrp prices")
		self.df_scraper_mkt  = gsheet.get_dataframe(scraper_mkt[0],scraper_mkt[1],scraper_mkt[2])
		self.df_mm_mkt       = gsheet.get_dataframe(mm_mkt[0],mm_mkt[1],mm_mkt[2])
		self.df_bo_rrp       = gsheet.get_dataframe(bo_rrp[0],bo_rrp[1],bo_rrp[2])
		self.df_scraper_mkt  = self.df_scraper_mkt.drop_duplicates(subset=['product_code'], keep='first')
		self.df_mm_mkt       = self.df_mm_mkt.drop_duplicates(subset=['product_sku'], keep='first')
		self.df_bo_rrp       = self.df_bo_rrp.drop_duplicates(subset=['product_sku'], keep='first')
		self.df_scraper_mkt['final price'] = pandas.to_numeric(self.df_scraper_mkt['final price'])
		self.df_mm_mkt['final mkt']        = pandas.to_numeric(self.df_mm_mkt['final mkt'])
		self.df_bo_rrp['bo_rrp']           = pandas.to_numeric(self.df_bo_rrp['bo_rrp'])
		self.df_bo_rrp['purchase_price']   = pandas.to_numeric(self.df_bo_rrp['purchase_price'])

	def apply_user_filtering(self):
		# First merge the two sheets
		self.engine_dataframe = pandas.merge(left=self.engine_dataframe, right=self.engine_filter, left_on='product_sku', right_on='sku', how='right')
		starting_nsku = self.engine_dataframe.shape[0]
		self.engine_dataframe = self.engine_dataframe.loc[self.engine_dataframe["to_upload"] == "Yes",:]
		filtered_nsku = self.engine_dataframe.shape[0]
		print_check(f"Pricing engine recommendations filtered from {starting_nsku} SKUs to {filtered_nsku} SKUs")

	def generate_upload_format(self):
		# Apply some reformatting to put back into the price_pivot format
		self.engine_dataframe.loc[:,"item_group_id"] = self.engine_dataframe["product_sku"]
		self.engine_dataframe.loc[:,"subscription_1_months"] = np.where(self.engine_dataframe["subscription_1_months_low"] == self.engine_dataframe["subscription_1_months_high"],    self.engine_dataframe["subscription_1_months_low"].astype(str)  , self.engine_dataframe["subscription_1_months_low"].astype(str)  + "," + self.engine_dataframe["subscription_1_months_high"].astype(str))
		self.engine_dataframe.loc[:,"subscription_3_months"] = np.where(self.engine_dataframe["subscription_3_months_low"] == self.engine_dataframe["subscription_3_months_high"],    self.engine_dataframe["subscription_3_months_low"].astype(str)  , self.engine_dataframe["subscription_3_months_low"].astype(str)  + "," + self.engine_dataframe["subscription_3_months_high"].astype(str))
		self.engine_dataframe.loc[:,"subscription_6_months"] = np.where(self.engine_dataframe["subscription_6_months_low"] == self.engine_dataframe["subscription_6_months_high"],    self.engine_dataframe["subscription_6_months_low"].astype(str)  , self.engine_dataframe["subscription_6_months_low"].astype(str)  + "," + self.engine_dataframe["subscription_6_months_high"].astype(str))
		self.engine_dataframe.loc[:,"subscription_12_months"] = np.where(self.engine_dataframe["subscription_12_months_low"] == self.engine_dataframe["subscription_12_months_high"], self.engine_dataframe["subscription_12_months_low"].astype(str) , self.engine_dataframe["subscription_12_months_low"].astype(str) + "," + self.engine_dataframe["subscription_12_months_high"].astype(str))
		self.engine_dataframe.loc[:,"subscription_18_months"] = np.where(self.engine_dataframe["subscription_18_months_low"] == self.engine_dataframe["subscription_18_months_high"], self.engine_dataframe["subscription_18_months_low"].astype(str) , self.engine_dataframe["subscription_18_months_low"].astype(str) + "," + self.engine_dataframe["subscription_18_months_high"].astype(str))
		self.engine_dataframe.loc[:,"subscription_24_months"] = np.where(self.engine_dataframe["subscription_24_months_low"] == self.engine_dataframe["subscription_24_months_high"], self.engine_dataframe["subscription_24_months_low"].astype(str) , self.engine_dataframe["subscription_24_months_low"].astype(str) + "," + self.engine_dataframe["subscription_24_months_high"].astype(str))

	def generate_eprice_dataframe(self):
		# Columns : Pricing Engine -> eprice export
		columns = {"sku"             : "item_group_id",
				   "category"        : "", 
				   "subcategory"     : "", 
				   "bulky"           : "", 
				   "store code"      : "", 
				   "new"             : "",
				   "months_old"      : "", 
				   "rrp"             : "", 
				   "plan1"           : "subscription_1_months",
				   "plan3"           : "subscription_3_months", 
				   "plan6"           : "subscription_6_months", 
				   "plan12"          : "subscription_12_months",
				   "plan18"          : "subscription_18_months", 
				   "plan24"          : "subscription_24_months", 
				   "old_low_plan1"   : "",
				   "old_low_plan3"   : "", 
				   "old_low_plan6"   : "",
				   "old_low_plan12"  : "", 
				   "old_low_plan18"  : "", 
				   "old_low_plan24"  : "",
				   "old_high_plan1"  : "", 
				   "old_high_plan3"  : "", 
				   "old_high_plan6"  : "", 
				   "old_high_plan12" : "", 
				   "old_high_plan18" : "", 
				   "old_high_plan24" : "",
				   "price change tag": "",
				   "price change reason": "",
				   'rrp_mm':"",
				   'rrp_scr':"",
				   'rrp_bo':""}

		# Create dataframe with columns
		self.df = pandas.DataFrame(columns=columns.keys())
		# Process our selected data
		for col in columns:
			pe_col = columns[col]
			if pe_col != "":
				self.df[col] = self.engine_dataframe[pe_col]
		
		# Set some of the values which are not available but needed
		# Store Codes
		self.df['store code'] = self.df['sku'].map(self.df_stores.set_index('product_sku')['stores'])
		# Category and Subcategory Names
		s = sku_data()
		self.df['category']    = self.df['sku'].map(s.df['category_name'])
		self.df['subcategory'] = self.df['sku'].map(s.df['subcategory_name'])
		# RRP Values
		self.df['rrp_scr']    = self.df['sku'].map(self.df_scraper_mkt.set_index('product_code')['final price'])
		self.df['rrp_mm']     = self.df['sku'].map(self.df_mm_mkt.set_index('product_sku')['final mkt'])
		self.df['rrp_bo']     = self.df['sku'].map(self.df_bo_rrp.set_index('product_sku')['bo_rrp'])
		self.df['purchase_price']     = self.df['sku'].map(self.df_bo_rrp.set_index('product_sku')['purchase_price'])
		self.df.loc[:,'rrp']  = self.df.loc[:,['rrp_scr','rrp_mm','rrp_bo']].min(axis=1)
		self.df.loc[:,'rrp']  = self.df.loc[:,'rrp'].fillna(self.df.loc[:,'purchase_price'])
		self.add_warning(self.df[self.df['rrp']=='']['sku'].to_list(), 'Cannot assign RRP value to product, so setting to -1')
		self.df.loc[:,'rrp']  = self.df.loc[:,'rrp'].fillna(-1)

		# Others
		# Make a string which timestamps the run day
		price_change_string = f"pricing engine {datetime.datetime.now().strftime('%y-%m-%d-%H%M')}"
		self.df["new"] = ""
		self.df['price change tag']    = price_change_string
		self.df['price change reason'] = price_change_string
		self.df['bulky']               = 0
		self.df = self.df.fillna('')

		# We also need to drop out any entries where there are no prices at all 
		# as this would indicate that we decativate the SKU which is not intended behaviour
		rows_before_drop = self.df.shape[0]
		# As we use strings, need to check if they are all empty, and then invert to drop them
		self.df = self.df[~(
							(self.df['plan1'].eq('')) & 
							(self.df['plan3'].eq('')) & 
							(self.df['plan6'].eq('')) & 
							(self.df['plan12'].eq('')) & 
							(self.df['plan18'].eq('')) & 
							(self.df['plan24'].eq(''))
							)]
		# Reset index as iloc used later
		self.df = self.df.reset_index(drop=True)
		rows_after_drop  = self.df.shape[0]
		if rows_before_drop != rows_after_drop:
			self.add_warning(['all'],f'Dropped {rows_before_drop - rows_after_drop} SKUs due to no prices being calculated')

		print (self.df)

	def add_warning(self, skus, info):
		# Singleton warning tracker
		wt = warning_tracker()
		# Empty list - Nothing to worry about
		if len(skus) == 0:
			return
		# Build message
		store = 'all'
		rp    = 'all'
		for sku in skus:
			wt.add_warning(warning_object('Pricing Engine',sku,'',store,rp,info))





