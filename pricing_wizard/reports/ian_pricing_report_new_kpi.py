	# Ian Connelly
	# 11 May 2022

def process(output_base, datafile, _end_date_s, _number_of_days, verbose=False):
	# Imports
	import pandas
	import functools
	import sys
	from reports.ian_pricing_report_utils import calcRelDisc, calcRelDiscBand, calcDiscount, getModeRentalPlan, clean, addDateCalculations
	from modules.print_utils import print_check, print_exclaim, tabulate_dataframe
	# Allow custom running
	today = pandas.to_datetime('today')
	today_s = f"{today.year}-{today.month}-{today.strftime('%d')}"

	# Convert format for dataframe selection
	end_date   = pandas.to_datetime(_end_date_s)
	start_date = end_date - pandas.Timedelta(days=_number_of_days)
	# Generate strings for naming convensions
	start_date_s = f"{start_date.year}-{start_date.month_name()}-{start_date.strftime('%d')}"
	end_date_s   = f"{end_date.year}-{end_date.month_name()}-{end_date.strftime('%d')}"

	# ---------------------- #
	# ----- Dataframe ------ #
	# ---------------------- #
	df = pandas.read_csv(datafile)

	# ---------------------- #
	# --- Sanity checks ---- #
	# ---------------------- #
	print_exclaim (f"Summary : Using date-range [{start_date_s}, {end_date_s})")

	# ---------------------- #
	# --- Date selection --- #
	# ---------------------- #
	dates = df["snapshot_date"].unique()
	print_check (f"Total days collected          : {len(dates)}")

	# ---------------------- #
	# ------ All SKUs ------ #
	# ---------------------- #
	SKUs = df["product_sku"].unique()
	print_check (f"Total number of products      : {len(SKUs)}")

	# ---------------------- #
	# ----- All stores ----- #
	# ---------------------- #
	stores = df["store_parent"].unique()
	print_check (f"Total number of stores        : {len(stores)}")

	# ---------------------- #
	# ----- Categories ----- #
	# ---------------------- #
	cats = df["category_name"].unique()
	print_check (f"Total number of categories    : {len(cats)}")
	subcats = df["subcategory_name"].unique()
	print_check (f"Total number of subcategories : {len(subcats)}")

	# ---------------------- #
	# --- Processing KPIs -- #
	# ---------------------- #

	# Convert to datetime object
	df["snapshot_date"] = pandas.to_datetime(df["snapshot_date"])

	# Sort by STORE, then SKU, then snapshot date
	df = df.sort_values(['store_parent','product_sku','snapshot_date'])

	# Apply the date selection
	df = df[(df["snapshot_date"] >= start_date) & (df["snapshot_date"] < end_date)]

	# ---------------------- #
	# --- Date selection --- #
	# ---------------------- #
	selected_dates = df["snapshot_date"].unique()
	total_days     = len(selected_dates)
	print_check (f"Dates reduced to              : {selected_dates}")
	print_check (f"Total number of days          : {total_days}")

	# ---------------------- #
	# -- Global variables -- #
	# ---------------------- #

	# Apply custom functions
	# Add boolean to identify discounted sales
	df["discount_1m"]  = df["m1_price"].apply(lambda x : True if "," in str(x) else False)
	df["discount_3m"]  = df["m3_price"].apply(lambda x : True if "," in str(x) else False)
	df["discount_6m"]  = df["m6_price"].apply(lambda x : True if "," in str(x) else False)
	df["discount_12m"] = df["m12_price"].apply(lambda x : True if "," in str(x) else False)
	df["discount_18m"] = df["m18_price"].apply(lambda x : True if "," in str(x) else False)
	df["discount_24m"] = df["m24_price"].apply(lambda x : True if "," in str(x) else False)

	# Calculate the discount amount (eg 0.1 = 10% discount)
	df["reldisc_1m"]   = df["m1_price"].apply(calcRelDisc)
	df["reldisc_3m"]   = df["m3_price"].apply(calcRelDisc)
	df["reldisc_6m"]   = df["m6_price"].apply(calcRelDisc)
	df["reldisc_12m"]  = df["m12_price"].apply(calcRelDisc)
	df["reldisc_18m"]  = df["m18_price"].apply(calcRelDisc)
	df["reldisc_24m"]  = df["m24_price"].apply(calcRelDisc)

	# Calculate price fraction (eg 0.9 = 90% regular price)
	df["discprice_1m"]   = df["m1_price"].apply(calcDiscount)
	df["discprice_3m"]   = df["m3_price"].apply(calcDiscount)
	df["discprice_6m"]   = df["m6_price"].apply(calcDiscount)
	df["discprice_12m"]  = df["m12_price"].apply(calcDiscount)
	df["discprice_18m"]  = df["m18_price"].apply(calcDiscount)
	df["discprice_24m"]  = df["m24_price"].apply(calcDiscount)

	# Calculate discount amount and bin into a grouping
	df["reldiscband_1m"]   = df["m1_price"].apply(calcRelDiscBand)
	df["reldiscband_3m"]   = df["m3_price"].apply(calcRelDiscBand)
	df["reldiscband_6m"]   = df["m6_price"].apply(calcRelDiscBand)
	df["reldiscband_12m"]  = df["m12_price"].apply(calcRelDiscBand)
	df["reldiscband_18m"]  = df["m18_price"].apply(calcRelDiscBand)
	df["reldiscband_24m"]  = df["m24_price"].apply(calcRelDiscBand)

	# Pricing session marker - Requires ordered data (market->sku->date)
	df['m1_price_session']   = (df['m1_price'].shift()  != df['m1_price']).cumsum()
	df['m3_price_session']   = (df['m3_price'].shift()  != df['m3_price']).cumsum()
	df['m6_price_session']   = (df['m6_price'].shift()  != df['m6_price']).cumsum()
	df['m12_price_session']  = (df['m12_price'].shift() != df['m12_price']).cumsum()
	df['m18_price_session']  = (df['m18_price'].shift() != df['m18_price']).cumsum()
	df['m24_price_session']  = (df['m24_price'].shift() != df['m24_price']).cumsum()

	# Cleaned price (ie rental price for session)
	df['m1_price_clean']  = df['m1_price'].apply(clean)
	df['m3_price_clean']  = df['m3_price'].apply(clean)
	df['m6_price_clean']  = df['m6_price'].apply(clean)
	df['m12_price_clean'] = df['m12_price'].apply(clean)
	df['m18_price_clean'] = df['m18_price'].apply(clean)
	df['m24_price_clean'] = df['m24_price'].apply(clean)

	# Make a default "order" which will reveal if no orders were placed (ie > 0 but < 1) and summed over all products in cats should still be < 1
	df['no_orders'] = 0.00001

	# ---------------------- #
	# --- Check ordering --- #
	# ---------------------- #
	if verbose:
		tabulate_dataframe(df[["snapshot_date","m1_price_session","m3_price_session","m6_price_session","m12_price_session","m18_price_session","m24_price_session","product_sku"]].head(40))

	# ---------------------- #
	# -- Check the format -- #
	# ---------------------- #
	if verbose:
		print_exlaim ("Data structure...")
		tabulate_dataframe (df.head())
		print_exclaim ("Columns in dataframe...")
		print_check (df.columns)
		print_exclaim ("Variable types of columns")
		print_check (df.dtypes)

	# ---------------------- #
	# -- Perform groupings - #
	# ---------------------- #

	# This performs a grouping
	cat_sub_group = df.groupby(["category_name","subcategory_name"])
	# Show the groupings constructed
	if verbose:
		print_check ("Categories and subcategories identified")
		print_check (cat_sub_group.groups.keys())

	# Groupby information
	# Access individual grouping for verbose/debug : g.get_group(<key>)
	# https://stackoverflow.com/questions/15259547/conditional-sums-for-pandas-aggregate
	# https://stackoverflow.com/questions/17266129/python-pandas-conditional-sum-with-groupby
	# https://keytodatascience.com/groupby-pandas-python#multiple-functions

	# ---------------------- #
	# -- Discount metrics -- #
	# ---------------------- #

	all_group = df.groupby(["store_parent","category_name","subcategory_name",'product_sku'], as_index=False).apply(
		lambda x : pandas.Series(dict(
		m12_discount_x_orders = ((x["reldisc_12m"] * x["m12_orders"]).sum()),
		m12_n_discount_orders = ((x[x["discount_12m"] == True]["m12_orders"]).sum()),
		m1_orders=(x["m1_orders"].sum()),
		m3_orders=(x["m3_orders"].sum()),
		m6_orders=(x["m6_orders"].sum()),
		m12_orders=(x["m12_orders"].sum()),
		m18_orders=(x["m18_orders"].sum()),
		m24_orders=(x["m24_orders"].sum()),
		no_orders=(x["no_orders"].sum())
		)))

	all_group["m12_average_discount_per_discounted_order"] = all_group["m12_discount_x_orders"]/all_group["m12_n_discount_orders"]
	all_group["mode_rental_plan"] = all_group[["m24_orders","m18_orders","m12_orders","m6_orders","m3_orders","m1_orders","no_orders"]].idxmax(axis=1)

	# Write out to a csv file
	# all_group.to_csv(f"{output_base}kpi-sku-{start_date_s}-{end_date_s}.csv")

	# Now group into subcategories and average over it
	subcat_group = all_group.groupby(["store_parent","category_name","subcategory_name"], as_index=False).apply(
		lambda x : pandas.Series(dict(
			m12_discount_x_orders = x["m12_discount_x_orders"].sum(),
			m12_n_discount_orders = x["m12_n_discount_orders"].sum(),
			m1_orders=(x["m1_orders"].sum()),
			m3_orders=(x["m3_orders"].sum()),
			m6_orders=(x["m6_orders"].sum()),
			m12_orders=(x["m12_orders"].sum()),
			m18_orders=(x["m18_orders"].sum()),
			m24_orders=(x["m24_orders"].sum()),
			no_orders=(x["m24_orders"].sum())
			))
		)

	subcat_group["m12_average_discount_per_discounted_order"] = subcat_group["m12_discount_x_orders"]/subcat_group["m12_n_discount_orders"]
	subcat_group["m12_discount_saturation"] = 100.0*subcat_group["m12_n_discount_orders"]/subcat_group["m12_orders"]
	subcat_group["mode_rental_plan"] = subcat_group[["m24_orders","m18_orders","m12_orders","m6_orders","m3_orders","m1_orders","no_orders"]].idxmax(axis=1)

	subcat_group.to_csv(f"{output_base}/kpi-sub-{start_date_s}-{end_date_s}.csv")

	# Now group into categories and group over it
	cat_group = all_group.groupby(["store_parent","category_name",], as_index=False).apply(
		lambda x : pandas.Series(dict(
			m12_discount_x_orders = x["m12_discount_x_orders"].sum(),
			m12_n_discount_orders = x["m12_n_discount_orders"].sum(),
			m1_orders=(x["m1_orders"].sum()),
			m3_orders=(x["m3_orders"].sum()),
			m6_orders=(x["m6_orders"].sum()),
			m12_orders=(x["m12_orders"].sum()),
			m18_orders=(x["m18_orders"].sum()),
			m24_orders=(x["m24_orders"].sum()),
			no_orders=(x["no_orders"].sum())
			))
		)

	cat_group["m12_average_discount_per_discounted_order"] = cat_group["m12_discount_x_orders"]/cat_group["m12_n_discount_orders"]
	cat_group["m12_discount_saturation"] = 100.0*cat_group["m12_n_discount_orders"]/cat_group["m12_orders"]
	cat_group["mode_rental_plan"] = cat_group[["m1_orders","m3_orders","m6_orders","m12_orders","m18_orders","m24_orders"]].idxmax(axis=1)

	# Storing data
	cat_group.to_csv(f"{output_base}/kpi-cat-{start_date_s}-{end_date_s}.csv")

	# --------------------------- #
	# - Pricing session metrics - #
	# --------------------------- #

	# To assess pricing session metrics, we need to group our data based on the rental plan pricing sessions
	# and evaluate this grouped data for each rental plan separately

	m1_session_group  = df.groupby(["store_parent","category_name","subcategory_name",'product_sku','m1_price', 'm1_price_clean', 'm1_price_session'], sort=False, as_index=False)
	m3_session_group  = df.groupby(["store_parent","category_name","subcategory_name",'product_sku','m3_price', 'm3_price_clean', 'm3_price_session'], sort=False, as_index=False)
	m6_session_group  = df.groupby(["store_parent","category_name","subcategory_name",'product_sku','m6_price', 'm6_price_clean', 'm6_price_session'], sort=False, as_index=False)
	m12_session_group = df.groupby(["store_parent","category_name","subcategory_name",'product_sku','m12_price','m12_price_clean','m12_price_session'], sort=False, as_index=False)
	m18_session_group = df.groupby(["store_parent","category_name","subcategory_name",'product_sku','m18_price','m18_price_clean','m18_price_session'], sort=False, as_index=False)
	m24_session_group = df.groupby(["store_parent","category_name","subcategory_name",'product_sku','m24_price','m24_price_clean','m24_price_session'], sort=False, as_index=False)

	# Calculate the total number of orders per pricing session and the startdate of the pricing session

	df_m1  = m1_session_group.apply(
		lambda x : pandas.Series(
			dict(
				m1_orders_sum = x["m1_orders"].sum(),
				m1_date_start = x["snapshot_date"].min()
				)))

	df_m3  = m3_session_group.apply(
		lambda x : pandas.Series(
			dict(
				m3_orders_sum = x["m3_orders"].sum(),
				m3_date_start = x["snapshot_date"].min()
				)))

	df_m6  = m6_session_group.apply(
		lambda x : pandas.Series(
			dict(
				m6_orders_sum = x["m6_orders"].sum(),
				m6_date_start = x["snapshot_date"].min()
				)))

	df_m12 = m12_session_group.apply(
		lambda x : pandas.Series(
			dict(
				m12_orders_sum = x["m12_orders"].sum(),
				m12_date_start = x["snapshot_date"].min()
				)))

	df_m18 = m18_session_group.apply(
		lambda x : pandas.Series(
			dict(
				m18_orders_sum = x["m18_orders"].sum(),
				m18_date_start = x["snapshot_date"].min()
				)))

	df_m24 = m24_session_group.apply(
		lambda x : pandas.Series(
			dict(
				m24_orders_sum = x["m24_orders"].sum(),
				m24_date_start = x["snapshot_date"].min()
				)))

	# Using the startdates in the pricing session grouped data, assess the date ranges for each pricing session
	df_m1  = addDateCalculations(df_m1,  "m1",  end_date)
	df_m3  = addDateCalculations(df_m3,  "m3",  end_date)
	df_m6  = addDateCalculations(df_m6,  "m6",  end_date)
	df_m12 = addDateCalculations(df_m12, "m12", end_date)
	df_m18 = addDateCalculations(df_m18, "m18", end_date)
	df_m24 = addDateCalculations(df_m24, "m24", end_date)


	# Evaluate metrics 
	# - the coefficient of variation - Using ddof = 0 for population stdev (avoid NaN for single price point rows)
	# - avg price over days - The average price weighted by the number of days active

	df_m1_sku = df_m1.groupby(["store_parent","category_name","subcategory_name",'product_sku'], as_index = False).apply(
			lambda x : pandas.Series(dict(
				m1_coeff = ( x['m1_price_clean'].std(ddof=0) / x['m1_price_clean'].mean()  ),
				m1_avg_price_over_days = ( (x["m1_price_clean"]*x["m1_days_in_session"]).sum() / x["m1_days_in_session"].sum() )
				)
			)
		)

	df_m3_sku = df_m3.groupby(["store_parent","category_name","subcategory_name",'product_sku'], as_index = False).apply(
			lambda x : pandas.Series(dict(
				m3_coeff = ( x['m3_price_clean'].std(ddof=0) / x['m3_price_clean'].mean()  ),
				m3_avg_price_over_days = ( (x["m3_price_clean"]*x["m3_days_in_session"]).sum() / x["m3_days_in_session"].sum() )
				)
			)
		)

	df_m6_sku = df_m6.groupby(["store_parent","category_name","subcategory_name",'product_sku'], as_index = False).apply(
			lambda x : pandas.Series(dict(
				m6_coeff = ( x['m6_price_clean'].std(ddof=0) / x['m6_price_clean'].mean()  ),
				m6_avg_price_over_days = ( (x["m6_price_clean"]*x["m6_days_in_session"]).sum() / x["m6_days_in_session"].sum() )
				)
			)
		)

	df_m12_sku = df_m12.groupby(["store_parent","category_name","subcategory_name",'product_sku'], as_index = False).apply(
			lambda x : pandas.Series(dict(
				m12_coeff = ( x['m12_price_clean'].std(ddof=0) / x['m12_price_clean'].mean()  ),
				m12_avg_price_over_days = ( (x["m12_price_clean"]*x["m12_days_in_session"]).sum() / x["m12_days_in_session"].sum() )
				)
			)
		)

	df_m18_sku = df_m18.groupby(["store_parent","category_name","subcategory_name",'product_sku'], as_index = False).apply(
			lambda x : pandas.Series(dict(
				m18_coeff = ( x['m18_price_clean'].std(ddof=0) / x['m18_price_clean'].mean()  ),
				m18_avg_price_over_days = ( (x["m18_price_clean"]*x["m18_days_in_session"]).sum() / x["m18_days_in_session"].sum() )
				)
			)
		)

	df_m24_sku = df_m24.groupby(["store_parent","category_name","subcategory_name",'product_sku'], as_index = False).apply(
			lambda x : pandas.Series(dict(
				m24_coeff = ( x['m24_price_clean'].std(ddof=0) / x['m24_price_clean'].mean()  ),
				m24_avg_price_over_days = ( (x["m24_price_clean"]*x["m24_days_in_session"]).sum() / x["m24_days_in_session"].sum() )
				)
			)
		)

	# Merging dataframes back - be wary of empty dataframes
	all_dfs = [ df_m1_sku, df_m3_sku, df_m6_sku, df_m12_sku, df_m18_sku, df_m24_sku, all_group]
	dfs = []

	for dfx in all_dfs:
		if not dfx.empty:
			dfs.append(dfx)

	df_merged = functools.reduce(lambda left,right: pandas.merge(left,right,on=["store_parent","category_name","subcategory_name",'product_sku'], how='outer'), dfs)
	df_merged.to_csv(f"{output_base}/kpi-sku-all-{start_date_s}-{end_date_s}.csv")
	print_exclaim(f"Processed data saved locally in {output_base}/kpi-sku-all-{start_date_s}-{end_date_s}.csv")



