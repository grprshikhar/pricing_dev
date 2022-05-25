import inquirer
from inquirer.themes import load_theme_from_dict
import json
import getpass
import sys

class options_handler(object):
	def __init__(self):
		self.current_user       = None
		self.current_sheet_type = None
		self.current_sheet      = None
		self.user_data_path     = "user_data.json"
		self.user_data          = None
		self.users              = None
		self.stage              = None
		self._theme             = None
		# Call setup
		self.setup()

	def setup(self):
		# Any setup options can go here rather than in init

		# Read json data
		try:
			self.user_data = json.load(open(self.user_data_path))
			self.users     = list(self.user_data.keys()) 
		except:
			print (f"Error reading user data from {self.user_data_path}")

		# Set theme for questions
		self._theme = load_theme_from_dict({
    					"Question": {
        					"mark_color": "yellow",
        					"brackets_color": "normal",},
    					"List": {
					        "selection_color": "black_on_bright_green",
        					"selection_cursor": "->"}
        					})
		self._theme2 = load_theme_from_dict({
    					"Question": {
        					"mark_color": "yellow",
        					"brackets_color": "normal",},
    					"List": {
					        "selection_color": "black_on_bright_red",
        					"selection_cursor": "->"}
        					})

	# Useful function for simple binary question
	def yn_question(self, question):
		question = [inquirer.List("yn", message=question, choices=["Yes","No"])]
		answer = inquirer.prompt(question, theme=self._theme, raise_keyboard_interrupt=True)
		if answer["yn"] == "Yes":
			return True
		else:
			return False

	def validate_user(self):
		# User validation expected to match existing data
		# Get the local username for validation
		local_username = getpass.getuser()
		# Create question
		question = [inquirer.List("user", message="Please select your name :", choices=self.users + ["None of the above"])]
		answer   = inquirer.prompt(question,theme=self._theme, raise_keyboard_interrupt=True)
		if answer["user"] != "None of the above":
			self.current_user = answer["user"]
		else:
			self.add_user_to_json()
		# Validate
		if self.user_data[self.current_user]["local_username"] != local_username:
			print (f"Error selecting {self.current_user} as local username is {local_username}.")
			print ("Please verify these details are correct.")
			sys.exit(1)
		else:
			print (f"User [{self.current_user}] verified.")

	def select_sheet(self):
		# Select the sheet
		sheet_options = list(self.user_data[self.current_user].keys())
		# Remove local_username used for verification
		sheet_options.remove("local_username")
		question = [inquirer.List("type", message="Select input type :", choices=sheet_options + ["Other"])]
		answer = inquirer.prompt(question, theme=self._theme, raise_keyboard_interrupt=True)
		self.current_sheet_type = answer["type"]
		if answer["type"] == "Other":
			self.current_sheet = input("Please enter SPREADSHEET_ID : ")
		else:
			self.current_sheet = self.user_data[self.current_user][answer["type"]]
			print (f"Selected {self.current_sheet_type} : {self.current_sheet}")
			question = [inquirer.List("yn", message="Proceed or update option :", choices=["Proceed","Update"])]
			answer = inquirer.prompt(question, theme=self._theme, raise_keyboard_interrupt=True)
			if answer["yn"] == "Update":
				new_id = input(f"Provide new id for {self.current_sheet_type} : ")
				self.user_data[self.current_user][self.current_sheet_type] = new_id
				self.current_sheet = new_id
				# Save updated data
				answer_yes = self.yn_question("Save updated data to disk :")
				if answer_yes:
					with open(self.user_data_path, 'w') as fp:
						json.dump(self.user_data, fp, indent=4)
				else:
					print (f"Data for [{self.current_user}] stored just for this session.")


	def add_user_to_json(self):
		# Take inputs and add to existing data
		name     = input("Please provide name : ")
		self.current_user = name
		self.user_data[name] = {}
		username = getpass.getuser()
		self.user_data[name]["local_username"] = username
		# Take template structure from Shikhar
		sheets = list(self.user_data["Shikhar"].keys())
		# Remove local_username used for verification
		sheets.remove("local_username")
		for s in sheets:
			user_sheet = input(f"Provide ID for {s} : ")
			self.user_data[name][s] = user_sheet

		# Ask for confirmation
		print ("Provided data...")
		print (f"{name} : {self.user_data[name]}")

		# Save data to disk or work in memory
		answer_yes = self.yn_question("Save updated data to disk :")
		if answer_yes:
			with open(self.user_data_path, 'w') as fp:
				json.dump(self.user_data, fp, indent=4)
		else:
			print (f"Data for [{self.current_user}] stored just for this session.")

	def get_running_stage(self):
		# This option can control the flow of the program
		# Just keep the order the same but can rename these without breaking code
		# Ensure "Exit" is last option as this looks best in terminal option
		stages = ["Upload e-price sheet", "Suggest price review SKUs", "Review Pricing Wizard data", "Exit"]
		question = [inquirer.List("stage", message="Please select your use case :", choices=stages)]
		answer = inquirer.prompt(question, theme=self._theme2, raise_keyboard_interrupt=True)
		self.stage = stages.index(answer["stage"])
		# Handle exit here
		if answer["stage"] == "Exit":
			sys.exit(0)

	# Getter functions
	def get_user(self):
		return self.current_user

	def get_sheet(self):
		return self.current_sheet

	def info(self):
		print ("---------------------")
		print ("Data Summary")
		print ("---------------------")
		print (f"Current user        : {self.current_user}")
		print (f"Selected sheet type : {self.current_sheet_type}")
		print (f"Sheet ID            : {self.current_sheet}")
		print ("---------------------")
		print ("All loaded data...")
		for user in self.user_data:
			print (f"--> {user}")
			for opt in sorted(self.user_data[user]):
				print (f"    \\-- {opt} : {self.user_data[user][opt]}")
		print ("---------------------")


