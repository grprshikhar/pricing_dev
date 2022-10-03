# Ian Connelly
# 20 May 2022

# file_1 is newer than file_2
def merge(file_1, file_2, outfile):

	# We will need to construct differences between time frames
	# This could be done in google sheets using complex vlookups
	# But we can also just load the CSV files into python
	# Generate merged datastructures on appropriate keys
	# Then calculate differences here

	import pandas
	import sys
	from modules.print_utils import print_check, print_exclaim

	print_exclaim (f"Difference: ({file_1} - {file_2})")

	# ---------------------- #
	# ----- Data frames ---- #
	# ---------------------- #

	# Define index when reading in as column 0
	df_1 = pandas.read_csv(file_1, index_col=[0])
	df_2 = pandas.read_csv(file_2, index_col=[0])

	# ---------------------- #
	# - Validate structure - #
	# ---------------------- #

	def check_dataframe(df, filename):
		n_rows    = len(df)
		columns   = df.columns
		n_columns = len(columns)
		print_check (f"Dataframe : {filename}")
		print_check (f"Rows      : {n_rows}")
		print_check (f"Columns   : {n_columns}")
		return n_rows, columns

	def check_data(n_rows_1, cols_1, n_rows_2, cols_2 ):
		# Check amount of data
		merge_opt = ""
		if n_rows_1 != n_rows_2:
			print_exclaim ("Different number of rows in dataframes.")
		else:
			print_check ("Matching number of rows.")
		if merge_opt == "":
			merge_opt = "left"
		print_check (f"Merging option : {merge_opt}")
		# Check columns
		matching_columns = set(cols_1) & set(cols_2)
		if len(cols_1) != len(cols_2):
			print_exclaim ("Different number of columns which is not expected.")
		# Merge key combination
		key_cols = "store_parent,category_name,subcategory_name,product_sku"
		# Split key columns if more than one given
		key_cols = key_cols.split(",")
		# Remove keys from comparison columns
		comparison_cols = list(set(matching_columns) - set(key_cols))
		print_check (f"Key column(s)        : {key_cols}")
		print_check (f"Comparison column(s) : {comparison_cols}")
		return merge_opt, key_cols, comparison_cols

	# Check and return some useful information (unpack output of check_dataframe with *)
	merge_opt, key_cols, comparison_cols = check_data(*check_dataframe(df_1, file_1), *check_dataframe(df_2, file_2))

	# Now perform the merging and check output
	df_merged = pandas.merge(left=df_1, right=df_2, on=key_cols, how=merge_opt, suffixes=("_x","_y"))

	cols_to_drop = []
	for col_name in sorted(comparison_cols):
		new_col_name = "delta_"+col_name
		x_col_name   = col_name+"_x"
		y_col_name   = col_name+"_y"
		# Only make numerical calculation if data type is numeric
		if pandas.api.types.is_numeric_dtype(df_merged[x_col_name]) and pandas.api.types.is_numeric_dtype(df_merged[y_col_name]):
			# Diff [1 - 2]
			df_merged[new_col_name] = df_merged[x_col_name] - df_merged[y_col_name]
			# Percentage diff [100*(1 - 2) / 2]
			df_merged["pct_"+new_col_name] = df_merged.apply(lambda x : 100.0*(x[x_col_name] - x[y_col_name])/x[y_col_name] if x[y_col_name] != 0 else "", axis=1)
			cols_to_drop.append(x_col_name)
			cols_to_drop.append(y_col_name)


	# Drop the old columns
	df_merged = df_merged.drop(columns=cols_to_drop)
	df_merged.to_csv(outfile)
	print_exclaim(f"Merged data written out to {outfile}")

