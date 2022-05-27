import modules.gsheet as gsheet
from modules.print_utils import print_check, print_green, print_warning, tabulate_dataframe
import pandas
import numpy

class GM_validator(object):
	# initialise with gsheet read
	def __init__(self, sheet_id, data_range='GM!A:AX', market='EU'):
		self.sheet_id   = sheet_id
		self.data_range = data_range
		self.market     = market
		self.get_data()
	
	# Pull data and get dataframe
	def get_data(self):	
		self.df = gsheet.get_dataframe(self.sheet_id, self.data_range)
		print_check(f"Pulled data for {self.market}")
		self.rename_columns()
		print_check(f"Found {self.df.shape[0]} new SKUs")


	def rename_columns(self):
		# Clean the header
		# EU structure
		if self.market == "EU":
			update = {"new prices"             : [12,13,14,15,16,17],
					  "new prices pp pct"      : [19,20,21,22,23,24],
					  "committed subs revenue" : [25,26,27,28,29,30],
					  "gross margin"           : [31,32,33,34,35,36],
					  "total committed"        : [37,38,39,40,41,42],
					  "gross margin pct"       : [43,44,45,46,47,48]}
		# US structure
		if self.market == "US":
			update = {"new prices"             : [ 9,10,11,12,13,14],
					  "new prices pp pct"      : [16,17,18,19,20,21],
					  "committed subs revenue" : [22,23,24,25,26,27],
					  "gross margin"           : [28,29,30,31,32,33],
					  "total committed"        : [34,35,36,37,38,39],
					  "gross margin pct"       : [40,41,42,43,44,45]}

		# Get header values
		header = self.df.columns.values
		# Clean the strings 
		# - strip (remove white space)
		# - replace (remove any .00)
		for i in range(0,len(header)): 
			header[i] = str(header[i]).strip().replace(".00","") 
		# Apply prefixes based on knowledge
		for prefix in update:
			for i in update[prefix]:
				header[i] = prefix+" "+header[i]
		
		# Reassign
		self.df.columns = header

	def select_SKUs(self, SKUs):
		# Build a query string
		query = "|".join(SKUs)
		# Pull out the dataframe the subset of data which matches
		df_skus = self.df[self.df['sku'].str.contains(query)]
		# Perform some validation about the request and response
		n_requested = len(SKUs)
		n_found     = df_skus.shape[0]
		# If we match the number requested and number found
		if n_requested == n_found:
			print_check("Found all requested SKUs")
		else:
			# Generate a set difference
			missing_skus = set(SKUs) - set(df_skus['sku'])
			# If it is empty, indicates we had duplicates provided by user
			if len(missing_skus) == 0:
				raise ValueError("Duplicate SKUs were provided.")
			# Otherwise we have some SKUs requested which were not in the sheet (maybe EU/US or mistyped)
			raise ValueError(f"Not all requested SKUs were found in {self.market} pricing sheet.\nMissing SKUs: {missing_skus}")
		# Store our new dataframe
		self.df_skus = df_skus.reset_index(drop=True)
		self.sanitise_SKUs()
		self.summarise()
		self.validate_SKUs()

	def validate_SKUs(self):
		any_errors   = []
		any_warnings = []

		# Check that bulky has been defined by catman
		bulk_err = self.check_bulky()
		any_errors.extend(bulk_err)

		# Check the gross margin percentages for all active plans
		gm_err, gm_warn = self.check_gross_margins(25,40)
		any_errors.extend(gm_err)
		any_warnings.extend(gm_warn)

		# Check the purchase price percentages for all active plans
		ppp_err = self.check_pp_perc()
		any_errors.extend(ppp_err)

		# Finalise the validation
		if any_warnings:
			print_warning("\n".join(any_warnings))
		if any_errors:
			raise ValueError("\n".join(any_errors))

	def check_bulky(self):
		any_errors = []
		if self.df_skus["bulky?"].isnull().values.any():
			skus = self.df_skus.loc[(self.df_skus["bulky?"].isnull()),"sku"]
			any_errors.append(f"Bulky column contains null values for SKUs : {skus.values}")
		if ~self.df_skus["bulky?"].isin([0,1]).values.any():
			skus = self.df_skus.loc[(~self.df_skus["bulky?"].isin([0,1])),"sku"]
			any_errors.append(f"Bulky column values are not 0 or 1 for SKUs : {skus.values}")

		return any_errors

	def check_gross_margins(self, min_threshold, threshold):
		any_errors   = []
		any_warnings = []
		for rp in [1,3,6,12,18,24]:
			# Check if any GM < 15% - error
			col_name = f"gross margin pct {rp}"
			if self.df_skus.loc[(self.df_skus[col_name] < min_threshold)].empty != True:
				skus = self.df_skus.loc[(self.df_skus[col_name] < min_threshold),'sku']
				any_errors.append(f"{rp}M - gross margin % is below the minimum threshold ({min_threshold}%) for SKUs : {skus.values}")

			if self.df_skus.loc[(self.df_skus[col_name] >= min_threshold) & (self.df_skus[col_name] < threshold)].empty != True:
				skus = self.df_skus.loc[(self.df_skus[col_name] >= min_threshold) & (self.df_skus[col_name] < threshold),'sku']
				any_warnings.append(f"{rp}M - gross margin % is low ({min_threshold} < GM% < {threshold}) for SKUs : {skus.values}")

		return any_errors, any_warnings

	def check_pp_perc(self):
		any_errors   = []
		for rp,ppp in [(1, 11),(3, 8),(6, 6),(12, 5),(18, 4.5),(24, 4)]:
			# Check if the purchase price % is lower than threshold reserved used for RRP (usually PP < RRP)
			col_name = f"new prices pp pct {rp}"
			if self.df_skus.loc[(self.df_skus[col_name] > ppp)].empty != True:
				skus = self.df_skus.loc[(self.df_skus[col_name] < ppp), 'sku']
				any_errors.append(f"{rp}M PP% is below the expected pricing threshold ({ppp}%) for SKUs : {skus.values}")

		return any_errors

	def summarise(self):
		print_green("Summary of new price data")
		sku_properties = self.df_skus.set_index('sku')[['category level 1','category level 2','bulky?','avg pp','rrp']]
		tabulate_dataframe(sku_properties)
		for rp in [1,3,6,12,18,24]:
			sku_rp = self.df_skus.set_index('sku')[[f"new prices {rp}", f"new prices pp pct {rp}", f"gross margin pct {rp}"]]
			tabulate_dataframe(sku_rp)

	def sanitise_SKUs(self):
		# We should place here any preprocessing/sanitisation required on the new dataframe
		# Remove sheets NaN error
		self.df_skus = self.df_skus.replace('#N/A',numpy.nan)
		# Clean string and convert types
		for rp in [1,3,6,12,18,24]:
			col_name = f"gross margin pct {rp}"
			self.df_skus[col_name] = self.df_skus[col_name].str.rstrip("%")
			self.df_skus[col_name] = pandas.to_numeric(self.df_skus[col_name],errors="coerce")
			col_name = f"new prices pp pct {rp}"
			self.df_skus[col_name] = self.df_skus[col_name].str.rstrip("%")
			self.df_skus[col_name] = pandas.to_numeric(self.df_skus[col_name],errors="coerce")
			col_name = f"new prices {rp}"
			self.df_skus[col_name] = self.df_skus[col_name].str.replace("€","",regex=False)
			self.df_skus[col_name] = self.df_skus[col_name].str.replace("$","",regex=False)
			self.df_skus[col_name] = pandas.to_numeric(self.df_skus[col_name],errors="coerce")
		# Other types
		self.df_skus["sku"]  			 = self.df_skus["sku"].astype(str)
		self.df_skus["name"] 			 = self.df_skus["name"].astype(str)
		self.df_skus["category level 1"] = self.df_skus["category level 1"].astype(str)
		self.df_skus["category level 2"] = self.df_skus["category level 2"].astype(str)
		self.df_skus["brand"]  			 = self.df_skus["brand"].astype(str)
		self.df_skus["bulky?"] 			 = pandas.to_numeric(self.df_skus["bulky?"], errors="coerce")
		self.df_skus["avg pp"] 			 = pandas.to_numeric(self.df_skus["avg pp"], errors="coerce")
		self.df_skus["rrp"] 			 = pandas.to_numeric(self.df_skus["rrp"],    errors="coerce")



