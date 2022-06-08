# System imports
import datetime
import pandas
# Module imports
import modules.gsheet as gsheet
import modules.gdrive as gdrive
import modules.catman_utils as catman_utils
import modules.sanity_checks as sanity_checks
import modules.redshift_manager as redshift_manager
import modules.admin_panel as admin_panel
from modules.print_utils import print_check, print_exclaim, print_green, tabulate_dataframe
from modules.eprice_update_utils import check_discount_anchor


class eprice_validator(object):
	# initialise with gsheet read or dataframe assignment (use named arguments!)
	def __init__(self, run_opts, sheet_id=None, data_range=None, dataframe=None):
		# Tools
		self.run_opts = run_opts
		self.redshift   = None
		self.admin_panel = None
		# Template file name when created
		self.template_filename = ""
		# Input for data
		if sheet_id and data_range:
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
		print_exclaim("Applying sanity checks to pricing sheet")
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
		# Check price plans are not below a threshold
		sanity_checks.check_minimum(self.df_td, 5)
		print_check("Rental plans larger than minimum requirement")
		# Clean NaN in new columns and set to empty strings
		self.df_td['new']= self.df_td['new'].fillna('')
		print_exclaim("Passed all checks\n")


	def post_sanity_checks(self):
		# Check against RedShift pricing history
		answer_yes = self.run_opts.yn_question("Check historical price points :")
		if answer_yes:
			# Create RedShift database manager (if not created)
			if not self.redshift:
				self.redshift = redshift_manager.redshift_manager(self.run_opts)
			# Connect the database
			self.redshift.connect()
			# Get the list of SKU for quicker request
			skus = self.df_td["sku"].unique().tolist()
			# Retrieve a dataframe consisting of min_high and max_high prices
			historical_sku_df = self.redshift.get_price_history(skus)
			# Now we need to process this data and check the recent high prices
			# TO-DO
			# If discount being applied, high price needs to be min_high
			check_discount_anchor(self.df_td, historical_sku_df)

			# If repricing being applied, high price _can_ be max_high

		# Check the RRP% using min/max limits
		plan_limit_dict = {
			1 :  [0.085, 0.5],
			3 :  [0.068, 0.3],
			6 :  [0.055, 0.16],
			12 : [0.034, 0.078],
			18 : [0.03,  0.054],
			24 : [0.025, 0.041]}
		answer_yes = self.run_opts.yn_question("Check RRP% guidelines :")
		if answer_yes:
			sanity_checks.check_rrp_perc(self.df_td, plan_limit_dict)
			print_check("Passed price % guidelines")

	def summarise(self):
		# Breakdown the output for review
		# - Summary of category/plans
		answer_yes = self.run_opts.yn_question("View upload data summary :")
		if answer_yes:
			sanity_checks.show_summary(self.df_td)

		# - Summary of statistics of data
		answer_yes = self.run_opts.yn_question("View upload data statistics :")
		if answer_yes:
			sanity_checks.show_stats(self.df_td)

		# - Show the sheet for final check
		answer_yes = self.run_opts.yn_question("View full upload data :")
		if answer_yes:
			disc_dt = self.df_td[['sku','store code','new','plan1','plan3','plan6','plan12','plan18','plan24']].copy()
			print_green("Full upload data")
			tabulate_dataframe(disc_dt)

	# Main "upload" function which manages the google drive and then admin panel uploads
	def upload(self):
		self.upload_template_to_gdrive()
		self.upload_template_to_adminpanel()

	def upload_template_to_gdrive(self):
		# Download the template file
		template_name = gdrive.download_store_template()
		# Read template into dataframe
		template_df   = pandas.read_excel(template_name, sheet_name=None)
		# Get the rental plan sheet
		rental_plans  = template_df["rental_plans"]
		# Fill data from our dataframe
		rental_plans[['SKU','Store code','Newness','1','3','6','12','18','24']] = self.df_td[['sku','store code','new','plan1','plan3','plan6','plan12','plan18','plan24']].copy()
		# Clean any NaN again
		rental_plans  = rental_plans.fillna('')
		# Configure output file name
		# Today date matching existing format could also use .date().isoformat()
		today_date    = datetime.datetime.today().strftime("%Y%m%d")
		# The user who is doing work
		username      = self.run_opts.current_user
		# Construct the file name
		out_filename  = f"{today_date}_{username}"
		# Ask for an optional additional descriptor to the filename
		description   = self.run_opts.text_question(f"Add optional descriptor to output filename [{out_filename}_<...>.xls] :")
		if description != "":
			out_filename += "_"+description+".xls"
		else:
			out_filename += ".xls"
		print_exclaim(f"Output file will be named [{out_filename}]")
		# Now save the file locally
		# NOTE - If we need xls output, we use xlwt package which is deprecated
		with pandas.ExcelWriter(out_filename) as writer:
			rental_plans.to_excel(writer, sheet_name="rental_plans",index=False)
		print_check("File written locally")
		# Store the local tempalte filename
		self.template_filename = out_filename
		# Now upload the file
		gdrive.upload(out_filename)
		# Should be done!
		print_check("File uploaded to Google Drive")

	def upload_template_to_adminpanel(self):
		# Create the admin panel tool (if not created)
		if not self.admin_panel:
			self.admin_panel = admin_panel.admin_panel(self.run_opts)
		# Generate standardized Admin Panel naming
		time_now        = datetime.datetime.today()
		today_date      = time_now.strftime("%Y%m%d")
		username        = self.run_opts.current_user
		adminPanelName  = f"PriWiz_{today_date}_{username}"
		description     = self.run_opts.text_question(f"Add optional descriptor to Admin Panel name [{adminPanelName}_<...>] :")
		if description != "":
			adminPanelName += "_"+description
		# Configure scheduled upload time - 5 minutes - Note we put into isoformat with milliseconds and add "Z" zone
		scheduledTime = (time_now + datetime.timedelta(minutes=5)).isoformat(timespec='milliseconds')+"Z"
		print_exclaim(f"Scheduled upload for 5 minutes time : {scheduledTime}")
		# Ask if we want a specific time
		answer_yes = self.run_opts.yn_question("Schedule upload for a specific time :")
		if answer_yes:
			time_string = self.run_opts.text_question("Provide the specificed date/time with format [YY-MM-dd:hh.mm] :")
			try:
				scheduledTime = datetime.datetime.strptime(time_string,"%y-%m-%d:%H.%M").isoformat(timespec='milliseconds')+"Z"
			except:
				raise ValueError(f"Scheduled time was not provided in correct strftime format [%y-%m-%d:%H.%M vs {time_string}]")
		# All information available so now we can proceed with passing to admin panel
		self.admin_panel.upload_pricing(pricingFileName = self.template_filename,
								        adminPanelName  = adminPanelName,
								        scheduledTime   = scheduledTime)
























