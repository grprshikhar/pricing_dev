# Potentially viable singleton instance
class sku_data(object):
	_instance    = None
	_initialised = False

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
		return cls._instance

	def __init__(self):
		if not self._initialised:
			import pandas
			import modules.gsheet as gsheet
			# Switch from product sheet to the central product info sheet
			self.sheet_id      = '1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew'
			self.data_range    = 'Product Data!A:E'
			self.df            = gsheet.get_dataframe(self.sheet_id, self.data_range, "SKU product data")
			self.config()
			self._initialised = True

	def print(self):
		print (self.df)

	def config(self):
		self.df = self.df.drop_duplicates(subset='product_sku')
		self.df = self.df.set_index('product_sku')

	def get_name(self, sku):
		try:
			name = self.df.loc[sku,'product_name']
			name = name[:50]
		except:
			name = 'Not found'
		return name

