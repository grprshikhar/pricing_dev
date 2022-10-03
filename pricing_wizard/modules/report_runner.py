# Testing
from reports.ian_pricing_report import ian_pricing_report

class report_runner(object):
	def __init__(self):
		self.reports = {"Pricing Report" : ian_pricing_report}

	def get_reports(self):
		return self.reports.keys()

	def run_report(self, key):
		# Initialise the class
		report = self.reports[key]()
		# Use the base function to setup redshift
		report.conn
		# Run the abstract method in all classes
		report.run_report()