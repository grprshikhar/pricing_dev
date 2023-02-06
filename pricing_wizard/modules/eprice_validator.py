# System imports
import datetime
import pytz
import pandas
import re
# Module imports
import modules.gsheet as gsheet
import modules.gdrive as gdrive
import modules.catman_utils as catman_utils
import modules.sanity_checks as sanity_checks
import modules.redshift_manager as redshift_manager
import modules.admin_panel as admin_panel
from modules.print_utils import print_check, print_exclaim, print_green, tabulate_dataframe
from modules.eprice_update_utils import check_discount_anchor, check_EU_rules
from modules.sqlite_logger import sqlite_logger


class eprice_validator(object):
	# initialise with gsheet read or dataframe assignment (use named arguments!)
	def __init__(self, run_opts, sheet_id=None, data_range=None, dataframe=None):
		# Tools
		self.run_opts    = run_opts
		self.is_partner  = self.run_opts.is_partner_upload
		self.redshift    = None
		self.admin_panel = None
		# Template file name when created
		self.template_filename = ""
		# Plan limit dictionary
		self.plan_limit_dict = {
			1 :  [0.06, 0.2],
			3 :  [0.05, 0.12],
			6 :  [0.04, 0.08],
			12 : [0.035, 0.075],
			18 : [0.03,  0.06],
			24 : [0.025, 0.05]}
		# EU data
		self.get_EU_legislation_data()

		# Input for data
		if sheet_id and data_range:
			self.sheet_id   = sheet_id
			self.data_range = data_range
			self.get_data()
		else:
			self.sheet_id   = None
			self.data_range = None
			self.set_data(dataframe)
			
	# Get days since discount data
	def get_EU_legislation_data(self):
		self.df_dsd   = gsheet.get_dataframe("1C6GKgcEO7HKn_Zfv3XmMd1tMoC_RGJQFfgkFQOoWVSA","A:C","Days since discount")
		self.df_30day = gsheet.get_dataframe("1XLpVyvbidRFt_Y0wm1gqL-DGqZBTObRdv84eDFhGEzw","A:N","30 day low price")

	# Assign dataframe
	def set_data(self, df):
		# Set data, then do the rest
		self.df = df
		self.checks()

	# Pull dataframe
	def get_data(self):
		# Pull data and get dataframe
		self.df = gsheet.get_dataframe(self.sheet_id, self.data_range, "Repricing sheet")
		self.checks()
		
	# Run consistent checks regardless of how dataframe is created
	def checks(self):
		# Run santisation of data
		self.sanitise()
		# Create the catman utils class object and attach
		self.catman_utils = catman_utils.catman_utils(self.is_partner)
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
		sanity_checks.check_minimum(self.df_td, 4)
		print_check("Rental plans larger than minimum requirement")
		# Check against plan limit dict
		sanity_checks.check_rrp_perc(self.df_td, self.plan_limit_dict)
		print_check(f"Checked price % guidelines")
		# Check if bulky 1M plan is high enough
		sanity_checks.bulky_plan_check(self.df_td)
		print_check("Checked bulky 1M price point (if applicable)")
		# Clean NaN in new columns and set to empty strings
		self.df_td['new']= self.df_td['new'].fillna('')
		# Check the price change tag is filled
		sanity_checks.check_price_change_tag(self.df_td)
		print_check("Price change tag checked")
		print_exclaim("Passed sanity checks")


	def post_sanity_checks(self):
		print_exclaim("Checking against current EU rule interpretation")
		check_EU_rules(self.df_td, self.df_dsd, self.df_30day)
		print_check("EU rule interpretation passed")			

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
			if self.is_partner:
				disc_dt = self.df_td[['sku','partner name','store code','new','plan1','plan3','plan6','plan12','plan18','plan24']].copy()
			else:
				disc_dt = self.df_td[['sku','store code','new','plan1','plan3','plan6','plan12','plan18','plan24']].copy()
			print_green("Full upload data")
			tabulate_dataframe(disc_dt)

	# Main "upload" function which manages the google drive and then admin panel uploads
	def upload(self):
		print_exclaim("Preparing to upload prices (use [CTRL+C] to cancel)")
		self.upload_template_to_gdrive()
		self.upload_template_to_adminpanel()
		self.upload_log()

	def upload_log(self):
		from modules.sqlite_logger import sqlite_logger
		s = sqlite_logger()
		s.upload()

	def upload_template_to_gdrive(self):
		# Partner upload has different handling if we are doing partner store codes or partner names
		is_partner_names = False
		# Download the template file
		if self.is_partner:
			is_partner_names = self.run_opts.yn_question("Do you want to upload using Partner Name?")
			if is_partner_names:
				# Get Partner template using Partner Name
				template_name = gdrive.download_partner_template()
			else:
				# Get Partner template using Store code
				template_name = gdrive.download_store_template()	
		else:
			# Get B2B/B2C template using Store code
			template_name = gdrive.download_store_template()
		# Read template into dataframe
		template_df   = pandas.read_excel(template_name, sheet_name=None)
		# Get the rental plan sheet
		rental_plans  = template_df["rental_plans"]
		# Fill data from our dataframe
		if self.is_partner:
			if is_partner_names:
				# Partner name into partner name column
				rental_plans[['SKU','Partner Name','Newness','1','3','6','12','18','24','Price Change Tag']] = self.df_td[['sku','partner name','new','plan1','plan3','plan6','plan12','plan18','plan24','price change tag']].copy()
			else:
				# Partner name into store code column
				rental_plans[['SKU','Store code','Newness','1','3','6','12','18','24','Price Change Tag']] = self.df_td[['sku','partner name','new','plan1','plan3','plan6','plan12','plan18','plan24','price change tag']].copy()
		else:
			# Store code into store code column
			rental_plans[['SKU','Store code','Newness','1','3','6','12','18','24','Price Change Tag']] = self.df_td[['sku','store code','new','plan1','plan3','plan6','plan12','plan18','plan24','price change tag']].copy()
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
		# Need the user to select Staging or Production version of site
		answer = self.run_opts.choice_question("Please select Admin Panel version for upload",["Production","Staging"])
		to_production = (answer == "Production")

		# Create the admin panel tool (if not created)
		if not self.admin_panel:
			self.admin_panel = admin_panel.admin_panel(self.run_opts, to_production)
			self.admin_panel.configure()
			
		# Generate standardized Admin Panel naming
		adminPanelName  = self.template_filename

		# Configure scheduled upload time - 5 minutes - Note we put into isoformat with milliseconds and add "Z" zone
		# print_exclaim(f"Scheduling upload for 1 minutes time")
		# Ask if we want a specific time
		answer_yes = self.run_opts.yn_question("Do you wish to upload prices immediately :")
		if not answer_yes:
			print_green(f"Provide time for upload in Berlin timezone")
			# Add a regex check for format
			pattern = re.compile(r'\d\d\-\d\d\-\d\d\:\d\d\.\d\d')
			# Generate a retry loop until its correct
			match = False
			while not match:
				# Get the user string
				time_string = self.run_opts.text_question("Provide the specified Berlin date/time with format [YY-MM-dd:hh.mm] :")
				# See if we found a full match (None type if no match found)
				match = (pattern.fullmatch(time_string) != None)

			# Now use the valid string but still catch error incase of problem
			try:
				# Create timezone object
				scheduledTime = datetime.datetime.strptime(time_string,"%y-%m-%d:%H.%M")
				# Convert to Berlin locale timezone object
				scheduledTime = pytz.timezone('Europe/Berlin').localize(scheduledTime,is_dst=None)
				# Now convert to UTC
				scheduledTime = scheduledTime.astimezone(pytz.utc)
				# Now format it for upload (:-6 strips off last 5 characters which are +00.00 for UTC, ie timezone)
				scheduledTime = scheduledTime.isoformat(timespec='milliseconds')[:-6]+"Z"
			except:
				print_exclaim(f"Scheduled time was not provided in correct strftime format [%y-%m-%d:%H.%M vs {time_string}]")
		else:
			#time_now      = datetime.datetime.utcnow()
			#time_now      = pytz.datetime.datetime.now(tz=pytz.timezone('Europe/Berlin')).replace(tzinfo=None)
			#scheduledTime = (time_now + datetime.timedelta(minutes=2)).isoformat(timespec='milliseconds')+"Z"
			#print(scheduledTime)
			# Setting null means we tell AdminPanel to upload 'Now'
			scheduledTime = "null"

		# All information available so now we can proceed with passing to admin panel
		self.admin_panel.upload_pricing(pricingFileName = self.template_filename,
								        adminPanelName  = adminPanelName,
								        scheduledTime   = scheduledTime)

		# sqlite logging for price uploads
		s = sqlite_logger()
		s.add_price_upload((datetime.datetime.utcnow() if scheduledTime == "null" else scheduledTime),
						   self.df_td[['sku','store code','new','plan1','plan3','plan6','plan12','plan18','plan24','price change tag']])
		print_check("Upload complete!")
























