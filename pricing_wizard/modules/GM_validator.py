import modules.gsheet as gsheet
from modules.print_utils import print_check

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
		self.rename_columns()
		print (self.df.head())
		print (self.df.dtypes)


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
			update = {}

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