# Potentially viable singleton instance
class warning_tracker(object):
	_instance    = None
	_initialised = False

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
		return cls._instance

	def __init__(self):
		if not self._initialised:
			import pandas
			self.warnings = []
			self.data     = pandas.DataFrame()
			self._initialised = True

	def add_warning(self, w):
		self.warnings.append(w.store())

	def clear(self):
		import pandas
		self.warnings = []
		self.data     = pandas.DataFrame()

	def build(self):
		import pandas
		self.data = pandas.concat(self.warnings, ignore_index=True)

	def print(self):
		if self.data.empty:
			self.build()
		print (self.data)



class warning_object(object):
	def __init__(self,w_type=None,p_sku=None,p_name=None,p_store=None,p_rentalplan=None,w_info=None):
		self.w_type  = w_type
		self.p_sku   = p_sku
		self.p_name  = p_name
		self.p_store = p_store
		self.w_info  = w_info
		self.p_rentalplan = p_rentalplan

	def update(self,w_type,p_sku,p_name,p_store,p_rentalplan,w_info):
		self.w_type  = w_type
		self.p_sku   = p_sku
		self.p_name  = p_name
		self.p_store = p_store
		self.w_info  = w_info
		self.p_rentalplan = p_rentalplan

	def store(self):
		import pandas
		return pandas.DataFrame(data = {'Warning':self.w_type,
										'Info':self.w_info,
										'SKU':self.p_sku,
										'Name':self.p_name,
										'Rental Plan':self.p_rentalplan,
										'Store':self.p_store}, index=[0])

