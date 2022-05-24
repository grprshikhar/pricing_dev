#! /usr/bin/env python3
# Import the option handler for managing user input
from modules.options_handler import options_handler as opts
# Import the eprice_validator for validating inputs
from modules.eprice_validator import eprice_validator

# ------------------------------------------------------------------------ #
# Functions managing calls for each stage of the program flow
# ------------------------------------------------------------------------ #
def validate_and_upload_eprice(run_opts):
	# Validate the user information
	run_opts.validate_user() 
	# Verify the URL to be used
	run_opts.select_sheet()
	# Create eprice validator and runs checks
	data_range = 'Export!A:N'
	validator = eprice_validator(run_opts.current_sheet, data_range)
	# Check output
	validator.summarise(run_opts)



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
	# Print out the title
	print_title()

	# Create object
	run_opts = opts()

	# Simple looping flow
	while True:
		# User provides a starting option (provides exit option)
		run_opts.get_running_stage()

		# 0 : Proceed with user details to validate and upload e-price sheet
		if run_opts.stage == 0:
			validate_and_upload_eprice(run_opts)

		# 1 : Provide potential to expand into redshift checks and suggest SKUs to be checked
		if run_opts.stage == 1:
			something_with_redshift(run_opts)

		# 2 : Just print out the data stored in the json file for cross-checks on-the-fly
		if run_opts.stage == 2:
			run_opts.info()

