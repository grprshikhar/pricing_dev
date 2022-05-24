#! /usr/bin/env python3
# Main program flow

def validate_and_upload_eprice(pricing_wizard):
	# Validate the user information
	pricing_wizard.validate_user() 
	# Verify the URL to be used
	pricing_wizard.select_sheet()


def something_with_redshift(pricing_wizard):
	pass

def print_title():
	# Imports for title
	from termcolor import colored,cprint
	from pyfiglet import figlet_format
	# Removed upper/lower bands because this does not respect user colour scheme
	cprint(figlet_format('  Pricing\n  Wizard!\n',font='starwars',width = 200 ), 'red', attrs=['bold'])

if __name__ == "__main__":
	# Print out the title
	print_title()
	# Import the option handler for managing user input
	from modules.options_handler import options_handler as opts
	# Create object
	pricing_wizard = opts()
	# Set up a program flow to switch between options or rerun choices
	while True:
		# User provides a starting option
		pricing_wizard.get_running_stage()

		# 0 : Proceed with user details to validate and upload e-price sheet
		if pricing_wizard.stage == 0:
			validate_and_upload_eprice(pricing_wizard)

		# 1 : Provide potential to expand into redshift checks and suggest SKUs to be checked
		if pricing_wizard.stage == 1:
			something_with_redshift(pricing_wizard)

		# 2 : Just print out the data stored in the json file for cross-checks on-the-fly
		if pricing_wizard.stage == 2:
			pricing_wizard.info()

