# On Mac, google drive will be mounted at /Volumes/GoogleDrive/My\ Drive/Pricing/Price\ Uploads/Price\ Upload\ -\ Sanity\ Checked/
# On Windows via Linux, not sure

import sqlite3
import datetime
from modules import gdrive

class sqlite_logger(object):
	def __init__(self):
		self.database = None
		self.location = None
		self.path     = None
		self.timeout  = 5
		self.user     = None
		self.initialise_tables()

	def download(self):
		gdrive.download_log(self.user)

	def upload(self):
		gdrive.upload_log(self.user)

	def make_connection(self, nretries):
		# Firstly set the user
		self.user     = open(".active_user.dat","r").readlines()[0].strip()
		self.path     = f"{self.user}_log.sqlite"
		# Download from gdrive ONCE (per pricing_wizard run)
		active        = open(".active_file.dat","r").readlines()[0].strip()
		if active == "False":
			self.download()
			# Set to True to avoid downloading again
			active_file = open(".active_file.dat","w")
			active_file.write("True")
			active_file.close()
		# Helper function to manage retries
		iattempt = 1
		while iattempt <= nretries:
			try:
				# Make connection
				self.database = sqlite3.connect(self.path,timeout=self.timeout)
				# Attempt to access for writing
				self.database.execute("BEGIN IMMEDIATE")
				return
			except:
				# If we error on execute, it means the database is in use and we need to retry
				print(f"Logging database currently in use. Retry attempt {iattempt}/{nretries}")
				iattempt += 1
		# If we still fail, we need to error
		raise ValueError("Error connecting to SQLITE logging database. Please investigate.")

	def initialise_tables(self):
		init_margins = """CREATE TABLE IF NOT EXISTS 
							   margins(TimeStamp DateTime,
							   				 ScheduledFor DateTime,
											 User TEXT,
											 product_sku TEXT,
											 store_code TEXT,
											 newness TEXT,
											 m1_margin TEXT,
											 m3_margin TEXT,
											 m6_margin TEXT,
											 m12_margin TEXT,
											 m18_margin TEXT,
											 m24_margin TEXT,
											 combined_margin TEXT,
											 price_change_tag TEXT,
											 price_change_reason TEXT,
											 id TEXT
											 )"""
		init_price_change = """CREATE TABLE IF NOT EXISTS 
							   price_changes(TimeStamp DateTime,
							   				 ScheduledFor DateTime,
											 User TEXT,
											 product_sku TEXT,
											 store_code TEXT,
											 newness TEXT,
											 rental_plan_1_month TEXT,
											 rental_plan_3_month TEXT,
											 rental_plan_6_month TEXT,
											 rental_plan_12_month TEXT,
											 rental_plan_18_month TEXT,
											 rental_plan_24_month TEXT,
											 price_change_tag TEXT,
											 price_change_reason TEXT,
											 id TEXT
											 )"""
		init_warnings = """CREATE TABLE IF NOT EXISTS 
						   warnings(TimeStamp DateTime,
						   			User TEXT,
						   			Module TEXT,
						   			Bypassed TEXT,
						   			product_sku TEXT,
						   			store_code TEXT,
						   			Warning TEXT,
						   			id TEXT
						   			)""" 
		# Generate database
		self.make_connection(5)
		# Generate write lock
		self.database.execute(init_margins)
		self.database.execute(init_price_change)
		self.database.execute(init_warnings)
		self.database.commit()
		# End write lock
		self.database.close()

	def add_price_upload(self, scheduledFor, df):
		# Generate write lock
		self.make_connection(5)
		timestamp = str(datetime.datetime.utcnow())
		ID        = open(".active_session.dat","r").readlines()[0].strip()
		# 'SKU','Store code','Newness','1','3','6','12','18','24','Price Change Tag'
		# 'sku','store code','new','plan1','plan3','plan6','plan12','plan18','plan24','price change tag'
		# Not currently using
		price_change_reason = ""
		for idx,row in df.iterrows():
			insertion = f"""INSERT INTO price_changes(TimeStamp,
													  User,
													  ScheduledFor,
													  product_sku,
													  store_code,
													  newness,
													  rental_plan_1_month,
													  rental_plan_3_month,
													  rental_plan_6_month,
													  rental_plan_12_month,
													  rental_plan_18_month,
													  rental_plan_24_month,
													  price_change_tag,
													  price_change_reason,
													  id
													  )
													  VALUES('{timestamp}',
													  		 '{self.user}',
													  		 '{scheduledFor}',
													  		 '{row['sku']}',
													  		 '{row['store code']}',
													  		 '{row['new']}',
													  		 '{row['plan1']}',
													  		 '{row['plan3']}',
													  		 '{row['plan6']}',
													  		 '{row['plan12']}',
													  		 '{row['plan18']}',
													  		 '{row['plan24']}',
													  		 '{row['price change tag']}',
													  		 '{price_change_reason}',
													  		 '{ID}'
													  		 )"""
			# Now insert
			self.database.execute(insertion)
		self.database.commit()
		# End write lock
		self.database.close()

	def add_warnings(self, user, bypassed, warning_str):
		import inspect
		import re
		sku_finder = re.compile(r"\bGRB\S+\b")
		market_finder = re.compile(r"\b(de|at|us|nl|es|business|business_at|business_us|business_nl|business_es)\b")
		# Get the function which called the print_warning (2 steps back)
		oringinator = inspect.stack()[2]
		func = oringinator.function
		ID   = open(".active_session.dat","r").readlines()[0].strip()
		# Get database handle
		self.make_connection(5)

		prefix = ""
		for w in warning_str.split("\n"):
			# Remove single quotes as breaks SQL
			w = w.replace("'","")

			# See if we can identify any SKU
			any_sku = sku_finder.findall(w)
			if any_sku:
				any_sku = " ".join(any_sku)
			else:
				any_sku = ""

			# See if we can identify any market
			any_market = market_finder.findall(w)
			if any_market:
				any_market = " ".join(any_market)
			else:
				any_market = ""

			# If nothing was found, treat this warning as prefix for future sku/markets 
			if any_sku == "" and any_market == "":
				prefix = w
			else:
				w = prefix + w

			# Timestamp (updates with milliseconds)
			timestamp = str(datetime.datetime.utcnow())
			
			insertion = f"""INSERT INTO warnings(TimeStamp,User,Module,Bypassed,product_sku,store_code,Warning,id)
							VALUES('{timestamp}','{self.user}','{func}','{bypassed}','{any_sku}','{any_market}','{w}','{ID}')"""
			self.database.execute(insertion)
		self.database.commit()
		self.database.close()

	def add_margins(self, scheduledFor, df):
		# Generate write lock
		self.make_connection(5)
		timestamp = str(datetime.datetime.utcnow())
		ID        = open(".active_session.dat","r").readlines()[0].strip()
		# 'SKU','Store code','Newness','1','3','6','12','18','24','Price Change Tag'
		# 'sku','store code','new','plan1','plan3','plan6','plan12','plan18','plan24','price change tag'
		# Not currently using
		price_change_reason = ""
		for idx,row in df.iterrows():
			insertion = f"""INSERT INTO margins(TimeStamp ,
								   				 ScheduledFor ,
												 User ,
												 product_sku ,
												 store_code ,
												 newness ,
												 m1_margin ,
												 m3_margin ,
												 m6_margin ,
												 m12_margin ,
												 m18_margin ,
												 m24_margin ,
												 combined_margin,
												 price_change_tag ,
												 price_change_reason ,
												 id 
													  )
													  VALUES('{timestamp}',
													  		 '{self.user}',
													  		 '{scheduledFor}',
													  		 '{row['sku']}',
													  		 '{row['store code']}',
													  		 '{row['new']}',
													  		 '{row['m1_margin']}',
													  		 '{row['m3_margin']}',
													  		 '{row['m6_margin']}',
													  		 '{row['m12_margin']}',
													  		 '{row['m18_margin']}',
													  		 '{row['m24_margin']}',
													  		 '{row['combined_margin']}',
													  		 '{row['price change tag']}',
													  		 '{price_change_reason}',
													  		 '{ID}'
													  		 )"""
			# Now insert
			self.database.execute(insertion)
		self.database.commit()
		# End write lock
		self.database.close()