# Class to hold methods for connecting to Amazon Redshift

from modules.print_utils import print_exclaim, print_check
from getpass import getpass
import redshift_connector
import pandas
import datetime

class redshift_manager(object):
	def __init__(self, run_opts):
		self.connection = None
		self.run_opts   = run_opts

	def connect(self):
		# Check if we already made a connection
		if self.connection:
			print_check("Reusing active database connection")
			return
		# Otherwise set up the connection
		print_exclaim("Preparing connection to RedShift database")
		user = self.run_opts.get_redshift_username()
		pwd  = getpass("Enter RedShift password :: ")
		self.connection = redshift_connector.connect(
						host='datawarehouse-production.cpbbk0zu5qod.eu-central-1.redshift.amazonaws.com',
						port=5439,
						database='dev',
						user=user,
						password=pwd,
						timeout=15
						)
		print_check("RedShift connection made.")

	# ----------------------------
	# Queries we will need to run
	# ----------------------------
	def get_price_history(self, skus=[]):
		# Get todays date
		today = datetime.datetime.today()
		# We need data over past 30 days, but its possible a full price was older before discounts so lets take a bit more data
		start_date_30 = ( today - datetime.timedelta(days=30) ).date().isoformat()
		start_date_60 = ( today - datetime.timedelta(days=60) ).date().isoformat()
		nskus = len(skus) if skus else "all"
		print_exclaim(f"Querying pricing history to find min-high price since {start_date_30} for {nskus} skus")
		# Split over lines to help readability (and ensure correct whitespace)
		query = []
		# Create query to extract the min high price over past 30 days
		query.append("select store_parent,product_sku,")
		query.append("min(case when rental_plan_price_1_month like '%,%' then split_part(rental_plan_price_1_month,',',2)::float else rental_plan_price_1_month::float end) min_high_1m,")
		query.append("min(case when rental_plan_price_3_months like '%,%' then split_part(rental_plan_price_3_months,',',2)::float else rental_plan_price_3_months::float end) min_high_3m,")
		query.append("min(case when rental_plan_price_6_months like '%,%' then split_part(rental_plan_price_6_months,',',2)::float else rental_plan_price_6_months::float end) min_high_6m,")
		query.append("min(case when rental_plan_price_12_months like '%,%' then split_part(rental_plan_price_12_months,',',2)::float else rental_plan_price_12_months::float end) min_high_12m,")
		query.append("min(case when rental_plan_price_18_months like '%,%' then split_part(rental_plan_price_18_months,',',2)::float else rental_plan_price_18_months::float end) min_high_18m,")
		query.append("min(case when rental_plan_price_24_months like '%,%' then split_part(rental_plan_price_24_months,',',2)::float else rental_plan_price_24_months::float end) min_high_24m,")
		query.append("min(case when rental_plan_price_1_month like '%,%' then split_part(rental_plan_price_1_month,',',1)::float else rental_plan_price_1_month::float end) min_low_1m,")
		query.append("min(case when rental_plan_price_3_months like '%,%' then split_part(rental_plan_price_3_months,',',1)::float else rental_plan_price_3_months::float end) min_low_3m,")
		query.append("min(case when rental_plan_price_6_months like '%,%' then split_part(rental_plan_price_6_months,',',1)::float else rental_plan_price_6_months::float end) min_low_6m,")
		query.append("min(case when rental_plan_price_12_months like '%,%' then split_part(rental_plan_price_12_months,',',1)::float else rental_plan_price_12_months::float end) min_low_12m,")
		query.append("min(case when rental_plan_price_18_months like '%,%' then split_part(rental_plan_price_18_months,',',1)::float else rental_plan_price_18_months::float end) min_low_18m,")
		query.append("min(case when rental_plan_price_24_months like '%,%' then split_part(rental_plan_price_24_months,',',1)::float else rental_plan_price_24_months::float end) min_low_24m")
		query.append("from pricing.all_pricing_grover_snapshots")
		query.append(f"where snapshot_date > '{start_date_30}'")
		if skus:
			query.append(f"""and product_sku in ('{"','".join(skus)}')""")
		query.append("group by store_parent, product_sku")
		query.append("order by store_parent, product_sku")
		# Whitespace between components
		final_query = " ".join(query)
		# Get cursor
		cursor = self.connection.cursor()
		# Execute query
		cursor.execute(final_query)
		# Query finished running
		print_check("Query complete")
		# Retrieve output into a dataframe
		df_minhigh_30 = cursor.fetch_dataframe()

		print_exclaim(f"Querying pricing history to find max-high price since {start_date_60} for {nskus} skus")
		# Split over lines to help readability (and ensure correct whitespace)
		query = []
		# Create query to extract the min high price over past 30 days
		query.append("select store_parent,product_sku,")
		query.append("max(case when rental_plan_price_1_month like '%,%' then split_part(rental_plan_price_1_month,',',2)::float else rental_plan_price_1_month::float end) max_high_1m,")
		query.append("max(case when rental_plan_price_3_months like '%,%' then split_part(rental_plan_price_3_months,',',2)::float else rental_plan_price_3_months::float end) max_high_3m,")
		query.append("max(case when rental_plan_price_6_months like '%,%' then split_part(rental_plan_price_6_months,',',2)::float else rental_plan_price_6_months::float end) max_high_6m,")
		query.append("max(case when rental_plan_price_12_months like '%,%' then split_part(rental_plan_price_12_months,',',2)::float else rental_plan_price_12_months::float end) max_high_12m,")
		query.append("max(case when rental_plan_price_18_months like '%,%' then split_part(rental_plan_price_18_months,',',2)::float else rental_plan_price_18_months::float end) max_high_18m,")
		query.append("max(case when rental_plan_price_24_months like '%,%' then split_part(rental_plan_price_24_months,',',2)::float else rental_plan_price_24_months::float end) max_high_24m")
		query.append("from pricing.all_pricing_grover_snapshots")
		query.append(f"where snapshot_date > '{start_date_60}'")
		if skus:
			query.append(f"""and product_sku in ('{"','".join(skus)}')""")
		query.append("group by store_parent, product_sku")
		query.append("order by store_parent, product_sku")
		# Whitespace between components
		final_query = " ".join(query)
		# Get cursor
		cursor = self.connection.cursor()
		# Execute query
		cursor.execute(final_query)
		# Query finished running
		print_check("Query complete")
		# Retrieve output into a dataframe
		df_maxhigh_60 = cursor.fetch_dataframe()

		# Join these two dataframes
		df = pandas.merge(df_minhigh_30, df_maxhigh_60,how="left",on=["store_parent", "product_sku"])
		# Check
		print (df.head(30))
		return df





