import modules.gsheet as gsheet
from modules.print_utils import print_check, print_green_bold, print_warning, tabulate_dataframe
from modules.bulky_checker import bulky_checker
import pandas
import numpy

class GM_validator(object):
	# initialise with gsheet read
	def __init__(self, sheet_id, data_range='GM!A:AX', market='EU'):
		self.sheet_id      = sheet_id
		self.data_range    = data_range
		self.market        = market
		self.bulky_checker = bulky_checker()
		self.get_data()
	
	# Pull data and get dataframe
	def get_data(self):	
		# Pull the data from google sheets
		self.df = gsheet.get_dataframe(self.sheet_id, self.data_range)
		print_check(f"Pulled data for {self.market}")
		# Format the column names for consistency
		self.rename_columns()
		print_check(f"Found {self.df.shape[0]} new SKUs")

	# Format the column names as we cannot automate this fully
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
		
		# Assign the renamed header to dataframe
		self.df.columns = header

		# Create a new 'bulky?' in US dataframe
		# Either set to 0 - fixed no-bulky
		# Or set to None which will generate a check
		if self.market == "US":
			self.df["bulky?"] = None

	# User provides SKUs which defines a subset of main dataframe
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
				print_warning("Duplicate SKUs were provided and removed.")
			else:
				# Otherwise we have some SKUs requested which were not in the sheet (maybe EU/US or mistyped)
				raise ValueError(f"Not all requested SKUs were found in {self.market} pricing sheet.\nMissing SKUs: {missing_skus}")
		# Store our new dataframe
		self.df_skus = df_skus.reset_index(drop=True)
		# Clean the dataframe
		self.sanitise_SKUs()
		# Validate the data for selected SKUs
		self.validate_SKUs()
		# Display a summary
		self.show_summary()

	def validate_SKUs(self):
		any_errors   = []
		any_warnings = []

		# Check that bulky has been defined by catman
		bulk_err, bulk_warn = self.check_bulky()
		any_errors.extend(bulk_err)
		any_warnings.extend(bulk_warn)

		# Check the gross margin percentages for all active plans
		gm_err, gm_warn = self.check_gross_margins(15,20) # 15% minimum, 20%+ ideal
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


	# --------------------------------------------
	# Functions to help with validation of data
	# --------------------------------------------
	def check_bulky(self):
		# Bulky does not seem to set very often (ever?) so will use the look up that eprice does
		any_errors = []
		any_warnings = []

		# If it is not present, we will set a value based on best knowledge
		if self.df_skus["bulky?"].isnull().values.any():
			skus = self.df_skus.loc[(self.df_skus["bulky?"].isnull()),"sku"]
			any_warnings.append(f"Checking bulky status for : {skus.values}")
			any_warnings.append(f"New bulky flag options")
			# If not set, we will try and look it up
			for sku in skus:
				self.df_skus.loc[(self.df_skus["sku"]==sku),"bulky?"] = self.bulky_checker.is_it_bulky(sku)
				# Report the changes as well
				any_warnings.append(f'{self.df_skus.loc[(self.df_skus["sku"]==sku),["sku","bulky?"]].values}')

		# If a value was set, we check that it was 0 or 1
		if ~self.df_skus["bulky?"].isin([0,1]).values.any():
			skus = self.df_skus.loc[(~self.df_skus["bulky?"].isin([0,1])),"sku"]
			any_errors.append(f"Bulky column values are not 0 or 1 for SKUs : {skus.values}")

		return any_errors, any_warnings


	# --------------------------------------------
	# Functions to help with validation of data
	# --------------------------------------------
	def check_gross_margins(self, min_threshold, threshold):
		any_errors   = []
		any_warnings = []
		for rp in [1,3,6,12,18,24]:
			# Check if any GM < 15% - error
			col_name = f"gross margin pct {rp}"
			if self.df_skus.loc[(self.df_skus[col_name] < min_threshold)].empty != True:
				skus = self.df_skus.loc[(self.df_skus[col_name] < min_threshold),'sku']
				any_errors.append(f"{rp:2}M - gross margin % is below the minimum threshold ({min_threshold}%) for SKUs : {skus.values}")

			if self.df_skus.loc[(self.df_skus[col_name] >= min_threshold) & (self.df_skus[col_name] < threshold)].empty != True:
				skus = self.df_skus.loc[(self.df_skus[col_name] >= min_threshold) & (self.df_skus[col_name] < threshold),'sku']
				any_warnings.append(f"{rp:2}M - gross margin % is low ({min_threshold} < GM% < {threshold}) for SKUs : {skus.values}")

		return any_errors, any_warnings


	# --------------------------------------------
	# Functions to help with validation of data
	# --------------------------------------------
	def check_pp_perc(self):
		any_errors   = []
		# rp - rental plan; ppp - purchase price percentage
		for rp,ppp in [(1, 11),(3, 8),(6, 6),(12, 5),(18, 4.5),(24, 4)]:
			# Check if the purchase price % is lower than threshold reserved used for RRP (usually PP < RRP)
			col_name = f"new prices pp pct {rp}"
			if self.df_skus.loc[(self.df_skus[col_name] < ppp)].empty != True:
				skus = self.df_skus.loc[(self.df_skus[col_name] < ppp), 'sku']
				any_errors.append(f"{rp:2}M - PP% is below the expected pricing threshold ({ppp}%) for SKUs : {skus.values}")

		return any_errors


	# --------------------------------------------
	# Functions to print summary of SKU data
	# --------------------------------------------
	def show_summary(self):
		print_green_bold("Summary of new price data")
		sku_properties = self.df_skus.set_index('sku')[['category level 1','category level 2','bulky?','avg pp','rrp']]
		tabulate_dataframe(sku_properties)
		for rp in [1,3,6,12,18,24]:
			sku_rp = self.df_skus.set_index('sku')[[f"new prices {rp}", f"new prices pp pct {rp}", f"gross margin pct {rp}"]]
			tabulate_dataframe(sku_rp)


	# --------------------------------------------
	# Functions to clean the dataframe
	# --------------------------------------------
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

	# --------------------------------------------
	# Functions to handle creation of e-price data
	# --------------------------------------------
	def generate_eprice_dataframe(self):
		# Columns : GM -> eprice export
		columns = {"sku"             : "sku",
				   "category"        : "category level 1", 
				   "subcategory"     : "category level 2", 
				   "bulky"           : "bulky?", 
				   "store code"      : "internationals", 
				   "new"             : "",
				   "months_old"      : "", 
				   "rrp"             : "rrp", 
				   "plan1"           : "new prices 1",
				   "plan3"           : "new prices 3", 
				   "plan6"           : "new prices 6", 
				   "plan12"          : "new prices 12",
				   "plan18"          : "new prices 18", 
				   "plan24"          : "new prices 24", 
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
				   "old_high_plan24" : ""}
		# Create dataframe with columns
		df_eprice = pandas.DataFrame(columns=columns.keys())
		# Process our selected data
		for eprice_col in columns:
			gm_col = columns[eprice_col]
			if gm_col != "":
				df_eprice[eprice_col] = self.df_skus[gm_col]

		# Now set "newness"
		df_eprice["new"] = "new"
		return df_eprice


























