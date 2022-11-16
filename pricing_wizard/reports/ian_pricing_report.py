# Run price report
from reports.report_base import report_base
from reports.ian_pricing_report_new_kpi import process
from reports.ian_pricing_report_merge import merge
from modules.print_utils import print_check, print_exclaim
from modules.gdrive import upload_csv_to_sheet
from modules.gsheet import get_dataframe
from datetime import date, timedelta

class ian_pricing_report(report_base):
	# Class constructor
	def __init__(self):
		super().__init__()
		self.folder     = "price_report_csv"
		self.today      = date.today().strftime("%Y-%m-%d")
		# To download limited data
		self.query_date = (date.today() - timedelta(days=28*3)).strftime("%Y-%m-%d")
		# Date today
		self.end_date_7day_1  = (date.today()).strftime("%Y-%m-%d")
		# Date 7 days ago
		self.end_date_7day_2  = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
		# Date 14 days ago
		self.end_date_7day_3  = (date.today() - timedelta(days=14)).strftime("%Y-%m-%d")
		# Date today
		self.end_date_28day_1 = (date.today()).strftime("%Y-%m-%d")
		# Date 28 days ago
		self.end_date_28day_2 = (date.today() - timedelta(days=28)).strftime("%Y-%m-%d")
		# Date 56 days ago
		self.end_date_28day_3 = (date.today() - timedelta(days=56)).strftime("%Y-%m-%d")
		# Dates with full month names
		self.end_date_7day_1_B  = (date.today()).strftime("%Y-%B-%d")
		self.end_date_7day_2_B  = (date.today() - timedelta(days=7)).strftime("%Y-%B-%d")
		self.end_date_7day_3_B  = (date.today() - timedelta(days=14)).strftime("%Y-%B-%d")
		self.end_date_28day_1_B = (date.today()).strftime("%Y-%B-%d")
		self.end_date_28day_2_B = (date.today() - timedelta(days=28)).strftime("%Y-%B-%d")
		self.end_date_28day_3_B = (date.today() - timedelta(days=56)).strftime("%Y-%B-%d")

	# Run the report
	def run_report(self):
		self.create_clean_folder()
		#self.get_data_from_redshift()
		self.get_data_from_gsheet()
		self.process_data()
		self.merge_data()
		self.upload()

	# Step 0
	def create_clean_folder(self):
		# Create the folder
		import os
		try:
			os.mkdir(self.folder)
		# If it exist, delete any files inside it
		except FileExistsError:
			import glob
			files = glob.glob(self.folder+"/*")
			for f in files:
				os.remove(f)

	# New Step 1
	def get_data_from_gsheet(self):
		df = get_dataframe("1GdXMrpIFKAWJDUGU763pV9_Jb4x2JeWQQjVKGnO2wyI","Data!A:S","Price review data")
		df.to_csv(self.folder+'/results.csv', mode='w', header=True, index=False)
		print_exclaim(f"Data saved locally in {self.folder}/results.csv")


	# Step 1
	def get_data_from_redshift(self):
		print_exclaim("Querying redshift for pricing session data")
		# Big ol query
		q=f"""WITH order_dt
     AS (SELECT store_id,
                product_sku,
                product_name,
                category_name,
                subcategory_name,
                brand,
                rental_period,
                Trunc(created_date) order_date,
                Count(*)            num_orders
         FROM   master.subscription s
         WHERE  Trunc(created_date) >= '{self.query_date}'
                AND status = 'ACTIVE'
         GROUP  BY 1, 2, 3, 4, 5, 7, 6, 8 
         ORDER  BY 1, 2, 3, 4, 5, 7, 6, 8), 
         product_names
     AS (SELECT DISTINCT product_sku,
                         product_name,
                         category_name,
                         subcategory_name,
                         brand
         FROM   master.variant)
	SELECT DISTINCT snapshot_date,
                p.store_parent,
                p.product_sku,
                v.product_name,
                v.category_name,
                v.subcategory_name,
                v.brand,
                rental_plan_price_1_month   AS m1_price,
                rental_plan_price_3_months  AS m3_price,
                rental_plan_price_6_months  AS m6_price,
                rental_plan_price_12_months AS m12_price,
                rental_plan_price_18_months AS m18_price,
                rental_plan_price_24_months AS m24_price,
                Sum(CASE
                      WHEN rental_period = 1 THEN num_orders
                    END)                    AS m1_orders,
                Sum(CASE
                      WHEN rental_period = 3 THEN num_orders
                    END)                    AS m3_orders,
                Sum(CASE
                      WHEN rental_period = 6 THEN num_orders
                    END)                    AS m6_orders,
                Sum(CASE
                      WHEN rental_period = 12 THEN num_orders
                    END)                    AS m12_orders,
                Sum(CASE
                      WHEN rental_period = 18 THEN num_orders
                    END)                    AS m18_orders,
                Sum(CASE
                      WHEN rental_period = 24 THEN num_orders
                    END)                    AS m24_orders
	FROM   pricing.all_pricing_grover_snapshots p
       JOIN pricing.store_mapper_live_state sm
         ON p.store_parent = sm.store_parent
       JOIN product_names v
         ON p.product_sku = v.product_sku
       LEFT JOIN order_dt o
              ON o.order_date = p.snapshot_date
                 AND p.product_sku = o.product_sku
                 AND sm.store_id = o.store_id
	WHERE  snapshot_date >= '{self.query_date}'
	GROUP  BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13
		"""
		# To be investigated
		# Assign to local variable as property decorator prevents resetting value
		cursor = self.cursor.execute(q)
		# Counter
		i = 1
		# Step
		n = 10000
		while True:
			df = cursor.fetch_dataframe(n)
			if df is None:
				break
			if i%100 == 0:
				print_check (f"Processed {i*n}...")
			if i == 1:
				df.to_csv(self.folder+'/results.csv', mode='w', header=True, index=False)
			else:
				df.to_csv(self.folder+'/results.csv', mode='a', header=False, index=False)
			i +=1
		print_exclaim(f"Data saved locally in {self.folder}/results.csv")

	# Step 2
	def process_data(self):
		process(self.folder, f'{self.folder}/results.csv', self.end_date_7day_1, 7)
		process(self.folder, f'{self.folder}/results.csv', self.end_date_7day_2, 7)
		process(self.folder, f'{self.folder}/results.csv', self.end_date_28day_1, 28)
		process(self.folder, f'{self.folder}/results.csv', self.end_date_28day_2, 28)


	# Step 3
	def merge_data(self):
		# 7 day comparison
		merge(f"{self.folder}/kpi-sku-all-{self.end_date_7day_2_B}-{self.end_date_7day_1_B}.csv", 
			  f"{self.folder}/kpi-sku-all-{self.end_date_7day_3_B}-{self.end_date_7day_2_B}.csv",
			  f"{self.folder}/merged-{self.end_date_7day_1_B}-7day.csv")
		# 28 day comparison
		merge(f"{self.folder}/kpi-sku-all-{self.end_date_28day_2_B}-{self.end_date_28day_1_B}.csv", 
			  f"{self.folder}/kpi-sku-all-{self.end_date_28day_3_B}-{self.end_date_28day_2_B}.csv",
			  f"{self.folder}/merged-{self.end_date_28day_1_B}-28day.csv")

	# Final step
	def upload(self):
		# Upload to shared area now
		print_exclaim("Uploading to google drive")
		upload_csv_to_sheet('1zqJ13Cu2bNezfe_S9_nZU5xCCsrDwua1',
							f"{self.folder}/merged-{self.end_date_7day_1_B}-7day.csv",
							f"merged-{self.end_date_7day_1_B}-7day.csv")
		print_check("Upload complete for 7 day price report")
		upload_csv_to_sheet('1zqJ13Cu2bNezfe_S9_nZU5xCCsrDwua1',
							f"{self.folder}/merged-{self.end_date_28day_1_B}-28day.csv",
							f"merged-{self.end_date_28day_1_B}-28day.csv")
		print_check("Upload complete for 28 day price report")





