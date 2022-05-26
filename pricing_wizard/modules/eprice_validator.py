import modules.gsheet as gsheet
import modules.catman_utils as catman_utils
import modules.sanity_checks as sanity_checks
from tabulate import tabulate
from termcolor import colored,cprint
from modules.print_utils import print_check

class eprice_validator(object):
	# initialise with gsheet read or dataframe assignment (use named arguments!)
	def __init__(self, sheet_id='default', data_range='Export!A:N', dataframe=None):
		if not dataframe:
			self.sheet_id   = sheet_id
			self.data_range = data_range
			self.get_data()
		else:
			self.sheet_id   = None
			self.data_range = None
			self.set_data(dataframe)		

	# Assign dataframe
	def set_data(self, df):
		# Set data, then do the rest
		self.df = df
		self.checks()

	# Pull dataframe
	def get_data(self):
		# Pull data and get dataframe
		self.df = gsheet.get_dataframe(self.sheet_id, self.data_range)
		self.checks()
		
	# Run consistent checks regardless of how dataframe is created
	def checks(self):
		# Run santisation of data
		self.sanitise()
		# Create the catman utils class object and attach
		self.catman_utils = catman_utils.catman_utils()
		# Run sanity checks
		self.sanity_check()

	def sanitise(self):
		# Convert any other text values to lower case
		self.df['category']    = self.df['category'].str.lower()
		self.df['subcategory'] = self.df['subcategory'].str.lower()
		# Ensure type - int
		self.df['bulky']       = self.df['bulky'].astype(int)
		# Ensure type - float
		self.df['rrp']         = self.df['rrp'].astype(float)

	def sanity_check(self):
		# Use catman utils and sanity check functions to ensure format is valid
		print("\nApplying sanity checks to pricing sheet\n")
		# Column type checks
		sanity_checks.check_dataType(self.df)
		print_check("No empty cells")
		# Check categories
		self.catman_utils.check_catnames(self.df)
		print_check("Correct category & sub-category names")  
		# Clean store plans 
		self.df_td = self.catman_utils.clean_store_plan(self.df)
		# Check discount pricing format
		sanity_checks.check_discounts(self.df_td)
		print_check("Discount values applied correctly")
		# Check rental plan hierarchy
		sanity_checks.check_plan_hierarchy(self.df_td)
		print_check("Plan price hierarchy maintained")
		# Check charm pricing (number ends in 9)
		sanity_checks.last_digit_9(self.df_td)
		print_check("Decimal digit ends with 9")
		# Clean any NaN (check if this is just generating empty string columns)
		self.df_td['new']= self.df_td['new'].fillna('')
		print_check("Passed all checks\n")


	def summarise(self, run_opts):
		# Check the RRP% using min/max limits
		plan_limit_dict = {
			1 :  [0.085, 0.5],
			3 :  [0.068, 0.3],
			6 :  [0.055, 0.16],
			12 : [0.034, 0.078],
			18 : [0.03,  0.054],
			24 : [0.025, 0.041]}
		answer_yes = run_opts.yn_question("Check RRP% guidelines :")
		if answer_yes:
			sanity_checks.check_rrp_perc(self.df_td, plan_limit_dict)

		# Breakdown the output for review
		# - Summary of category/plans
		answer_yes = run_opts.yn_question("View upload data summary :")
		if answer_yes:
			sanity_checks.show_summary(self.df_td)

		# - Summary of statistics of data
		answer_yes = run_opts.yn_question("View upload data statistics :")
		if answer_yes:
			sanity_checks.show_stats(self.df_td)

		# - Show the sheet for final check
		answer_yes = run_opts.yn_question("View full upload data :")
		if answer_yes:
			disc_dt = self.df_td[['sku','store code','new','plan1','plan3','plan6','plan12','plan18','plan24']].copy()
			print(colored("Full upload data\n",'green')+colored(tabulate(disc_dt, headers='keys', tablefmt='psql'),'blue')+"\n\n") 






