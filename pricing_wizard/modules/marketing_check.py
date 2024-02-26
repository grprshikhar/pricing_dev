import modules.gsheet as gsheet
from modules.print_utils import print_check, tabulate_dataframe, print_exclaim

class marketing_check(object):
	def __init__(self):
		self.sheet_id   = '1RzseMI77nhAF9rn32mG1wYGGZiOz4PKSGIQy__XR8MY'
		self.data_range = 'Pricing_output'
		self.config()

	def config(self):
		self.df = gsheet.get_dataframe(self.sheet_id, self.data_range,'Pulling active marketing campaigns')

	def perform_check(self, d):
		print_exclaim("Checking price changes against active marketing campaign(s)")
		# Compare out price change SKUs against the marketing data
		price_change_skus = d['sku'].drop_duplicates().to_list()
		# Active campaigns
		active_campaign_skus = self.df[self.df['sku'].isin(price_change_skus)]
		# Check size
		if active_campaign_skus.empty:
			print_check("No SKUs identified in active marketing campaign(s)")
			return d
		# If not, we need input
		print_exclaim("The following SKUs are part of active marketing campaign(s)")
		tabulate_dataframe(active_campaign_skus)
		from modules.options_handler import options_handler
		__run_opts = options_handler()
		answer = __run_opts.choice_question('Please select one of the following actions :',['Remove campaign SKUs from upload','Keep campaign SKUs in upload','Cancel upload'])
		if 'Remove' in answer:
			print_exclaim(f"Dropping the following SKUs {active_campaign_skus}")
			d = d.drop(d[d['sku'].isin(active_campaign_skus['sku'].to_list())].index.to_list())
			print_check("SKUs are removed from upload")
			return d
		elif 'Keep' in answer:
			print_exclaim(f"Upload will continue with the following SKUs {active_campaign_skus}")
			return d
		else:
			raise ValueError("Exiting Pricing Wizard")
