# Class to hold methods for connecting to Amazon Redshift

from modules.print_utils import print_exclaim, print_check
from getpass import getpass
import redshift_connector
import datetime

class redshift_manager(object):
	def __init__(self):
		self.connection = None

	def connect(self):
		# Check if we already made a connection
		if self.connection:
			print_check("Reusing active database connection")
			return
		# Otherwise set up the connection
		print_exclaim("Preparing connection to RedShift database")
		user = input("Enter RedShift username :: ")
		pwd  = getpass("Enter RedShift password :: ")
		self.connection = redshift_connector.connect(
						host='datawarehouse-production.cpbbk0zu5qod.eu-central-1.redshift.amazonaws.com',
						port=5439,
						database='dev',
						user=user,
						password=pwd,
						timeout=5
						)
		print_check("RedShift connection made.")

	# ----------------------------
	# Queries we will need to run
	# ----------------------------
	def get_price_history(self, skus=[]):
		# Get todays date
		today = datetime.datetime.today()
		# We need data over past 30 days, but its possible a full price was older before discounts so lets take a bit more data
		start_date = ( today - datetime.timedelta(days=60) ).date().isoformat()
		nskus = len(skus) if skus else "all"
		print_exclaim(f"Querying pricing history from {start_date} for {nskus} skus")
		# Split over lines to help readability (and ensure correct whitespace)
		query = []
		query.append("select distinct snapshot_date,product_sku,store_parent,rental_plans,")
		query.append("rental_plan_price_1_month,rental_plan_price_3_months,rental_plan_price_6_months,")
		query.append("rental_plan_price_12_months,rental_plan_price_18_months,rental_plan_price_24_months")
		query.append("from pricing.all_pricing_grover_snapshots")
		query.append(f"where snapshot_date > '{start_date}'")
		if skus:
			query.append(f"""and product_sku in ('{"','".join(skus)}')""")
		query.append("group by 1,2,3,4,5,6,7,8,9,10")
		query.append("order by 1,2")
		# Whitespace between components
		final_query = " ".join(query)
		# Get cursor
		cursor = self.connection.cursor()
		# Execute query
		cursor.execute(final_query)
		# Query finished running
		print_check("Query complete")
		# Retrieve output into a dataframe
		df = cursor.fetch_dataframe()
		return df