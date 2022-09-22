# Class to handle price review clustering
import pandas
import itertools
import modules.gsheet as gsheet
from modules.options_handler import options_handler
from modules.print_utils import tabulate_dataframe, print_check, print_exclaim
import modules.gsheet as gsheet
# Clustering
from sklearn.cluster import Birch, KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np

class price_reviewer(object):
	def __init__(self):
		self.sheet_id = "1zB8QTkvXZXQc0ttdAIePuuuUhokhnHxHkrerO4CEeeg"
		self.ranges   = ["Product Data!A:AI","Marketing&Performance!A:AO"]
		self.cat      = ""
		self.sub      = ""
		self.market   = ""
		self.upload_id = '1aZ5Js5mFuD1o63kJD8ehS5KK-wk-XlmZuhEoIsEK1LY'
		self.get_data()
		self.create_variables()
		self.apply_selection()
		#self.separate_low_MoS_SKU()
		self.apply_clustering()

	def get_data(self):
		# Multiple sheets
		dfs = []
		for sheet_range in self.ranges:
			dfs.append(gsheet.get_dataframe(self.sheet_id, sheet_range, sheet_range.split("!")[0]))
		# Now merge on variant sku
		self.df = dfs[0]
		self.df = self.df.merge(dfs[1], right_on='variant_sku', left_on='variant_sku', suffixes=("","_r"), validate='one_to_one')
		# Drop entries where no category
		self.df = self.df[self.df['category_name'] != ""]

	def create_variables(self):
		# Months of stock
		self.df['created_subs_last_4weeks'] = pandas.to_numeric(self.df['created_subs_last_4weeks'], errors='coerce')
		self.df['stock_on_hand']            = pandas.to_numeric(self.df['stock_on_hand'], errors='coerce')
		self.df['created_subs_last_4weeks'] = self.df['created_subs_last_4weeks'].fillna(0)
		self.df['stock_on_hand']            = self.df['stock_on_hand'].fillna(0)
		self.df['months_of_stock']          = self.df['stock_on_hand'].divide(self.df['created_subs_last_4weeks']).replace(np.inf, 100)

	def separate_low_MoS_SKU(self):
		# We should remove low MoS SKUs before clustering
		MoS_threshold = 1
		self.df_low_mos = self.df[self.df['months_of_stock'] < MoS_threshold].copy() 
		self.df_low_mos['cluster_label'] = -1
		self.df         = self.df[self.df['months_of_stock'] >= MoS_threshold]


	def apply_selection(self):
		# Ask questions to reduce dataframe
		oh = options_handler()
		# Select market
		selected_market = oh.choice_question("Select market",["EU","US"])
		if selected_market == "EU":
			self.df = self.df[self.df['upcs'] == ""]
		if selected_market == "US":
			self.df = self.df[self.df['upcs'] != ""]
		# Generate lists after splitting on market
		cats    = self.df['category_name'].drop_duplicates().values.tolist()
		subcats = self.df[['category_name','subcategory_name']].drop_duplicates().values.tolist()
		# Select category
		selected_cat    = oh.choice_question("Select category",sorted(cats))
		# Create subcat list for this category
		subset_subcats  = ['All']
		subset_subcats.extend( sorted([x[1] for x in subcats if x[0] == selected_cat]) )
		# Select possible subcategory
		selected_subcat = oh.choice_question("Select subcategory",subset_subcats)
		# Reduce dataframe by category
		self.df = self.df[self.df['category_name'] == selected_cat]
		# Reduce dataframe by subcategory (if required)
		if selected_subcat != 'All':
			self.df = self.df[self.df['subcategory_name'] == selected_subcat]
		# Store selections
		self.market = selected_market
		self.cat    = selected_cat
		self.sub    = selected_subcat


	def get_features(self):
		features = ["months_of_stock",
					"avg_days_in_stock",
					"incoming_qty",
					"created_subs_last_4weeks",
					"stock_on_hand"]
		return features

	def numerify(self):
		# Convert types - needed for cleaning data
		for f in self.get_features():
			self.df[f] = pandas.to_numeric(self.df[f],errors='coerce')
		# Now set nan to 0
		self.df = self.df.fillna(0)

	def apply_clustering(self):
		# Clean
		self.numerify()
		# Features for clustering
		features = self.get_features()
		# Clustering tool
		cl = Birch(n_clusters=None, threshold=2.0, branching_factor=100)

		# Pandas returns fortran-style array 
		df_X = self.df[features].values
		# We need C-type array, this numpy function does this
		df_X = np.ascontiguousarray(df_X,dtype=np.float32)
		# Run the clustering and generate labels (apply scaling to help clustering)
		ss   = StandardScaler()
		df_Y = cl.fit_predict(ss.fit_transform(df_X))
		# Place labels onto the rows (ordering preserved)
		self.df['cluster_label'] = df_Y
		# Add back the low month of stock data
		#self.df = pandas.concat([self.df, self.df_low_mos], ignore_index=True)
		# Reclean
		self.numerify()
		# Sort
		self.df = self.df.sort_values(['cluster_label','variant_sku'])

	def summarise(self):
		group_summary = self.df.groupby(['cluster_label'])
		tabulate_dataframe(group_summary[self.get_features()].describe(percentiles=[]).T)
		# Options handling
		oh = options_handler()
		# Display cluster entries
		cluster_summary = self.df['cluster_label'].value_counts()
		cluster_ids = ['All']
		for cluster,value in sorted(cluster_summary.items(), key = lambda x: x[0]):
			cluster_ids.append(f"{cluster} : [{value}]")
		while True:
			print_exclaim("Group [-1] are all SKU with less than 1 month of stock")
			selected_id = oh.choice_question("Select cluster to display", cluster_ids+['Exit'])
			if selected_id == 'Exit':
				break
			else:
				self.show_cluster(selected_id)

		# Plot
		do_plot = oh.yn_question("Generate cluster plots?")
		if do_plot:
			print_exclaim("Generating 2D scatter plots of cluster variables")
			self.plot()
		print_exclaim(f"Uploading cluster results to [{self.upload_id}]")
		self.send_data_to_gsheet()
		print_check("Upload complete")

	def show_cluster(self, cluster_id):
		cluster_id = cluster_id.split(":")[0].strip()
		# Output features
		out_features = ["variant_sku","brand","product_name","cluster_label"]+self.get_features()
		if cluster_id != "All":
			cluster_id = int(cluster_id)
			cluster_df = self.df[self.df['cluster_label'] == cluster_id]
		else:
			cluster_df = self.df.sort_values(by=['cluster_label'])
		cluster_df_output = cluster_df[out_features]
		tabulate_dataframe(cluster_df_output)


	def plot(self):
		features = self.get_features()
		for perms in itertools.combinations(features, 2):
			x = perms[0]
			y = perms[1]
			# Make plot
			ax = self.df.plot.scatter(x,y,c='cluster_label', colormap='gist_rainbow')
			ax.get_figure().savefig(f"cluster_{x}_{y}.pdf")

	def send_data_to_gsheet(self):
		# Generate a tab based on cat or subcat name
		tab_name = f"{self.market} "
		if self.sub == "All":
			tab_name += f"{self.cat}"
		else:
			tab_name += f"{self.sub}"
		# Create tab in sheet (if does not exist)
		gsheet.create_tab_in_gsheet(self.upload_id,tab_name)
		# Place the cluster earlier in the column list
		self.df.insert(1, 'cluster_label', self.df.pop('cluster_label'))
		# Send data to gsheet
		gsheet.upload_df_to_gsheet(self.df, self.upload_id, tab_name+"!A:BZ")
		# Done





