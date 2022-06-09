import modules.gsheet as gsheet
from modules.print_utils import print_check

# When pricing new SKUs, product bulkiness is not always listed 
# BUT - we can look it up!
class bulky_checker(object):
	def __init__(self):
		self.sheet_id   = "153fzJOWK7HFnNil_LMd6sLz1kOFz4ZVBxy-etsCnIGA"
		self.data_range = "Pricing!A2:K" # We only actually need column A and K (but multi range get is a pain)
		self.get_dataframe()

	def get_dataframe(self):
		# Pull sheet for a larger range than needed
		self.df = gsheet.get_dataframe(self.sheet_id, self.data_range)
		# Drop other columns
		self.df = self.df.filter(["product_sku","size"])
		# Keep only the skus marked as bulky
		self.find_bulky_skus()

	def find_bulky_skus(self):
		self.df = self.df[(self.df["size"] == "Bulky")].reset_index(drop=True)
		print_check(f"Registered {self.df.shape[0]} bulky SKUs to use as reference")

	def is_it_bulky(self,sku):
		# Pass in a sku and we will check against the reference and return [0,1]
		# If it is empty, then the sku was not listed as bulky - return 0
		if self.df[self.df['product_sku'].str.contains(sku)].empty == True:
			return 0
		# Otherwise it was present, so return 1
		else:
			return 1

