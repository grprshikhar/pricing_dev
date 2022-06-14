# Utility functions to allow update of the dataframe being used for validation
from modules.options_handler import options_handler
from modules.print_utils import print_warning

# ------------------------------------------------------------------------------------
# This function shall apply the checks required by EU Directive 98/6/EC, amendment 6a
# ------------------------------------------------------------------------------------
def check_discount_anchor(df_main, df_ref):
	any_warnings = []
	# df_main - The dataframe created and passed through validation
	# df_ref  - The dataframe which contains the historical pricing information
	# Create a deep copy to work on
	df_copy = df_main.copy(deep=True)
	# Extrack the market - sku combinations
	market_sku = df_copy[["store code", "sku"]].values
	# Pricing columns
	rp_plans = [1,3,6,12,18,24]
	for market, sku in market_sku:
		for rp in rp_plans:
			col_main   = f"plan{rp}"
			col_ref    = f"min_high_{rp}m"
			col_ref_2  = f"min_low_{rp}m"
			# Get the value of "col_main" for entry of "market,sku"
			value_main = df_copy.loc[(df_copy["store code"] == market) & (df_copy["sku"] == sku), col_main].values[0]
			# Pass over null entries
			if value_main == "":
				continue
			# Extract the high price only for discounts (EU legislation does not apply to pure repricing up/down)
			if "," in value_main:
				high_main = float(value_main.split(",")[1])
			else:
				continue
			# Get the reference value
			value_ref   = df_ref.loc[(df_ref["store_parent"] == market) & (df_ref["product_sku"] == sku), col_ref].values[0]
			high_ref    = float(value_ref)
			value_ref_2 = df_ref.loc[(df_ref["store_parent"] == market) & (df_ref["product_sku"] == sku), col_ref_2].values[0]
			low_ref     = float(value_ref_2)

			# Compare
			if high_main > low_ref:
				any_warnings.append(f"{market} {sku} {rp:2}M rental plan is not using lowest 30 day price : {value_main} vs {low_ref}")
				if high_main == high_ref:
					nchar = len(market+" "+sku+" ")
					any_warnings.append("".ljust(nchar)+f"{rp:2}M rental plan : use of lowest high price [{high_ref}] may be acceptable for promotion extention")

	# Report
	if any_warnings:
		print_warning("\n".join(any_warnings))