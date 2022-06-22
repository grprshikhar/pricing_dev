
#! /usr/bin/env python3
# Regular modules
import sys
import readchar
# Import the option handler for managing user input
from modules.options_handler import options_handler as opts
# Import the eprice_validator for validating inputs
from modules.eprice_validator import eprice_validator
# Import the GM_validator for validating new pricing
from modules.new_price_validator import new_price_validator
# Error handling
from modules.print_utils import exception_hook
# Import module holding reports
from modules.report_runner import report_runner

# ------------------------------------------------------------------------ #
# Functions managing calls for each stage of the program flow
# ------------------------------------------------------------------------ #
def validate_and_upload_eprice(run_opts):
	# Validate the user information
	run_opts.validate_user() 
	# Verify the URL to be used
	run_opts.select_eprice_sheet()
	# Create eprice validator and runs checks
	data_range = 'Export!A:P'
	validator = eprice_validator(run_opts=run_opts, sheet_id=run_opts.current_sheet, data_range=data_range)
	# Run post-sanity checks
	validator.post_sanity_checks()
	# Display the output
	validator.summarise()
	# Upload output to google drive and admin panel
	validator.upload()

def price_new_skus(run_opts):
	# Validate the user information
	run_opts.validate_user()
	# Verify the URL to be used
	run_opts.select_new_price_sheet()
	# Create Catman GM tool and run checks
	if run_opts.new_price_market == "US":
		data_range = '3.GM!A8:AT'
	if run_opts.new_price_market == "EU":
		data_range = '3.GM!A8:AX'
	# Set up validation tool
	validator = new_price_validator(run_opts.current_sheet, data_range, run_opts.new_price_market)
	# Ask for SKUs if we have loaded the sheet
	SKUs = run_opts.get_SKUs()
	# Select the data
	validator.select_SKUs(SKUs)
	# Create e-price dataframe
	eprice_df = validator.generate_eprice_dataframe()
	# Pass into e-price validator
	ep_validator = eprice_validator(run_opts=run_opts, dataframe=eprice_df)
	# Run post-sanity checks
	ep_validator.post_sanity_checks()
	# Display the output
	ep_validator.summarise()
	# Upload output to google drive and admin panel
	ep_validator.upload()


def redshift_report(run_opts):
	# Class to manage setting up report options
	reports = report_runner()
	# User selects the report
	report_key = run_opts.choice_question("Select report :", reports.get_reports())
	# Run the report requested
	reports.run_report(report_key)

def print_title():
	# Imports for title
	from termcolor import colored,cprint
	from pyfiglet import figlet_format
	# Removed upper/lower bands because this does not respect user colour scheme
	cprint(figlet_format('  Pricing\n  Wizard!\n',font='starwars',width = 200 ), 'red', attrs=['bold'])

def reassign_keystrokes():
	# It seems some platforms indicate backspace differently
	# inquirer uses readchar to catch inputs
	# OSX - uses \x7F not \x08
	if sys.platform == "darwin":
		readchar.key.BACKSPACE = '\x7F'
	if sys.platform == "linux":
		readchar.key.BACKSPACE = '\x7F'

def suppress_pandas_xlwt_warning():
	# Asked to use .xls for AdminPanel upload
	# `xlwt` package required to write but deprecated in favour of .xlsx writing
	# This option suppresses the warning otherwise written
	import warnings
	warnings.simplefilter(action='ignore', category=FutureWarning)
	import pandas
	pandas.options.io.excel.xls.writer = 'xlwt'

# ------------------------------------------------------------------------ #
# Main program - control program flow
# ------------------------------------------------------------------------ #
if __name__ == "__main__":
	# Set exception hook for main program
	sys.excepthook = exception_hook
	# Reassign backspace key based on OS - WIP
	reassign_keystrokes()
	# Suppress xls warning once
	suppress_pandas_xlwt_warning()
	# Create object
	run_opts = opts()

	# Simple looping flow
	while True:
		# Print out the title when we restart loop
		print_title()
		# User provides a starting option (provides exit option)
		run_opts.get_running_stage()

		# 0 : Proceed with user details to validate and upload e-price sheet
		if run_opts.stage == 0:
			validate_and_upload_eprice(run_opts)

		# 1 : Handle pricing new SKUs
		if run_opts.stage == 1:
			price_new_skus(run_opts)

		# 2 : Run a redshift-based report
		if run_opts.stage == 2:
			redshift_report(run_opts)

		# 3 : Separate option for pricing review
		if run_opts.stage == 3:
			pass

		# 4 : Just print out the data stored in the json file for cross-checks on-the-fly
		if run_opts.stage == 4:
			run_opts.info()

