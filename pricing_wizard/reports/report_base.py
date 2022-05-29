# Base class to hold abstract methods for future redshift projects
from abc import ABC, abstractmethod
# Prevent override in some cases
from typing import final
# Redshift connector for python
import redshift_connector
# Password 
import getpass
# Modules
from modules.print_utils import print_check

class report_base(ABC):

	# Required for derived class
	@abstractmethod
	def __init__(self):
		self._conn = None
		pass

	# Redshift connection
	@property # Shared property in derived classes
	@final    # Cannot be changed in derived classes
	def conn(self):
		print_check("Configure RedShift connection.")
		user = input("Enter username : ")
		pwd  = getpass.getpass()
		# Make connection (required VPN)
		self._conn = redshift_connector.connect(
			host='datawarehouse-production.cpbbk0zu5qod.eu-central-1.redshift.amazonaws.com',
			port=5439,
			database='dev',
			user=user,
			password=pwd
			)
		print_check("RedShift connection active.")

	# Cursor from the redshift conection
	@property # Shared property in derived classes
	@final    # Cannot be changed in derived classes
	def cursor(self):
		if not self._conn:
			self.conn
		return self._conn.cursor()


	# Required for derived class
	@abstractmethod
	def run_report(self):
		pass