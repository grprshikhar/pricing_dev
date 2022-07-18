# On Mac, google drive will be mounted at /Volumes/GoogleDrive/My\ Drive/Pricing/Price\ Uploads/Price\ Upload\ -\ Sanity\ Checked/
# On Windows via Linux, not sure

import sqlite3
import datetime

class sqlite_logger(object):
	def __init__(self):
		self.database = None
		self.path     = "database.sqlite"
		self.timeout  = 60
		self.initialise_tables()

	def initialise_tables(self):
		init_price_change = """CREATE TABLE IF NOT EXISTS 
							   price_changes(TimeStamp DateTime,
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
											 price_change_reason TEXT
											 )"""
		init_warnings = """CREATE TABLE IF NOT EXISTS 
						   warnings(TimeStamp DateTime,
						   			User TEXT,
						   			Module TEXT,
						   			Bypassed TEXT,
						   			Warning TEXT
						   			)"""
		# Generate database
		self.database = sqlite3.connect(self.path,timeout=self.timeout)
		# Generate write lock
		self.database.execute("BEGIN IMMEDIATE")
		self.database.execute(init_price_change)
		self.database.execute(init_warnings)
		self.database.commit()
		# End write lock
		self.database.close()

	def add_price_upload(self, user, df):
		# Generate write lock
		self.database = sqlite3.connect(self.path,timeout=self.timeout)
		self.database.execute("BEGIN IMMEDIATE")
		timestamp = str(datetime.datetime.utcnow())
		# 'SKU','Store code','Newness','1','3','6','12','18','24','Price Change Tag'
		for idx,row in df.iterrows():
			print (row)
			print (row['SKU'])
			insertion = f"""INSERT INTO price_changes(TimeStamp,
													  User,
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
													  price_change_reason
													  )
													  VALUES('{timestamp}',
													  		 '{user}',
													  		 '{row['SKU']}',
													  		 '{row['Store code']}',
													  		 '{row['Newness']}',
													  		 '{row['1']}',
													  		 '{row['3']}',
													  		 '{row['6']}',
													  		 '{row['12']}',
													  		 '{row['18']}',
													  		 '{row['24']}',
													  		 '{row['Price Change Tag']}',
													  		 '{row['Price Change Reason']}'
													  		 )"""
			# Now insert
			self.database.execute(insertion)
		self.database.commit()
		# End write lock
		self.database.close()

	def add_warnings(self, user, bypassed, warning_str):
		import inspect
		stack = inspect.stack()
		oringinator = stack[2]
		func = oringinator.function
		self.database = sqlite3.connect(self.path,timeout=self.timeout)
		self.database.execute("BEGIN IMMEDIATE")
		for w in warning_str.split("\n"):
			timestamp = str(datetime.datetime.utcnow())
			# Remove single quotes as breaks SQL
			w = w.replace("'","")
			insertion = f"""INSERT INTO warnings(TimeStamp,User,Module,Bypassed,Warning)
							VALUES('{timestamp}','{user}','{func}','{bypassed}','{w}')"""
			self.database.execute(insertion)
		self.database.commit()
		self.database.close()
		

