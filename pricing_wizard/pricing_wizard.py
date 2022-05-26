#! /usr/bin/env python3
# Regular modules
import sys
# Import the option handler for managing user input
from modules.options_handler import options_handler as opts
# Import the eprice_validator for validating inputs
from modules.eprice_validator import eprice_validator
# Import the GM_validator for validating new pricing
from modules.GM_validator import GM_validator
# Error handling
from modules.print_utils import exception_hook

# ------------------------------------------------------------------------ #
# Functions managing calls for each stage of the program flow
# ------------------------------------------------------------------------ #
def validate_and_upload_eprice(run_opts):
	# Validate the user information
	run_opts.validate_user() 
	# Verify the URL to be used
	run_opts.select_eprice_sheet()
	# Create eprice validator and runs checks
	data_range = 'Export!A:N'
	validator = eprice_validator(sheet_id=run_opts.current_sheet, data_range=data_range)
	# Check output
	validator.summarise(run_opts)
	# Next step would be upload...
	# validator.upload(run_opts)

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
	validator = GM_validator(run_opts.current_sheet, data_range, run_opts.new_price_market)
	# Ask for SKUs if we have loaded the sheet
	SKUs = run_opts.get_SKUs()


def something_with_redshift(pricing_wizard):
	pass

def print_title():
	# Imports for title
	from termcolor import colored,cprint
	from pyfiglet import figlet_format
	# Removed upper/lower bands because this does not respect user colour scheme
	cprint(figlet_format('  Pricing\n  Wizard!\n',font='starwars',width = 200 ), 'red', attrs=['bold'])

# ------------------------------------------------------------------------ #
# Main program - control program flow
# ------------------------------------------------------------------------ #
if __name__ == "__main__":
	# Set exception hook for main program
	sys.excepthook = exception_hook

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

		# 2 : Provide potential to expand into redshift checks and suggest SKUs to be checked
		if run_opts.stage == 2:
			something_with_redshift(run_opts)

		# 3 : Just print out the data stored in the json file for cross-checks on-the-fly
		if run_opts.stage == 3:
			run_opts.info()

