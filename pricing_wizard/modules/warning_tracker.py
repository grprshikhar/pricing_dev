class warning_tracker(object):
	def __init__(self):
		import pandas
		self.warnings = []
		self.data     = pandas.DataFrame()

	def add_warning(self, w):
		self.warnings.append(w)

	def clear(self):
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
	def __init__(self,w_type=None,p_sku=None,p_name=None,p_store=None,w_info=None):
		self.w_type  = w_type
		self.p_sku   = p_sku
		self.p_name  = p_name
		self.p_store = p_store
		self.w_info  = w_info

	def update(self,w_type,p_sku,p_name,p_store,w_info):
		self.w_type  = w_type
		self.p_sku   = p_sku
		self.p_name  = p_name
		self.p_store = p_store
		self.w_info  = w_info

	def store(self):
		import pandas
		return pandas.DataFrame(data = {'Warning':self.w_type,
										'Info':self.w_info,
										'SKU':self.p_sku,
										'Name':self.p_name,
										'Store':self.p_store}, index=[0])

