# Utility functions to allow update of the dataframe being used for validation
from modules.options_handler import options_handler
from modules.print_utils import print_warning
import numpy as np

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


def check_EU_rules(df, df_dsd, df_30day, df_median_high_price_30day):
    # Propagating old prices from export sheet (or they are nan from new pricing)
    any_warnings = []
    df_copy = df.copy(deep=True)
    market_sku = df_copy[["store code", "sku"]].values
    rp_plans = [1, 3, 6, 12, 18, 24]
    for market, sku in market_sku:
        # Discount allowed flag
        # If the SKU is present, we need to check the flag
        try:
            discount_allowed = (
                True
                if df_dsd.loc[(df_dsd["product_sku"] == sku), "new_discount_allowed"].values[0] == 1
                else False
            )
        # If the SKU is not present, it means no discount ever made, so it's fine to apply
        except:
            discount_allowed = True
        # Lowest pricing data
        lowest_prices = df_30day.loc[
            (df_30day["store_parent"] == market) & (df_30day["product_sku"] == sku)
        ]

        for rp in rp_plans:
            # Column names for use
            col_active_low_price = f"active_plan{rp}"
            col_active_high_price = f"high_plan{rp}"
            col_old_low_price = f"old_low_plan{rp}"
            col_old_high_price = f"old_high_plan{rp}"
            # Retrieve values
            active_low_price = df_copy.loc[
                (df_copy["store code"] == market) & (df_copy["sku"] == sku), col_active_low_price
            ].values[0]
            active_high_price = df_copy.loc[
                (df_copy["store code"] == market) & (df_copy["sku"] == sku), col_active_high_price
            ].values[0]
            old_low_price = df_copy.loc[
                (df_copy["store code"] == market) & (df_copy["sku"] == sku), col_old_low_price
            ].values[0]
            old_high_price = df_copy.loc[
                (df_copy["store code"] == market) & (df_copy["sku"] == sku), col_old_high_price
            ].values[0]

            # Skip if nan because this means the plan is not being used or not applying a discount
            if np.isnan(active_low_price) or np.isnan(active_high_price):
                continue

            # Additional check for identical low and high, indicating a single price only
            if active_low_price == active_high_price:
                continue

            # NEW CHECK: Check if the current plan high price is greater than the median high price
            col_median_high_price_30day = f"m{rp}_median_high_price"
            try:
                median_high_price_30day = float(
                    df_median_high_price_30day.loc[
                        (df_median_high_price_30day["product_sku"] == sku), col_median_high_price_30day
                    ].values[0]
                )
                if active_high_price > median_high_price_30day:
                    any_warnings.append(
                        f"{market} {sku} {rp:2}M rental plan : High price violates EU law : [{active_high_price} vs median {median_high_price_30day}]"
                    )
            except:
                any_warnings.append(
                    f"{market} {sku} {rp:2}M rental plan : Median high price for the past 30 days is missing."
                )

            # Was there a discount running previously - was the old high price larger than the old low price
            prev_discount = old_high_price > old_low_price

            # If yes - Check that the new low price is lower than the old low price
            if prev_discount:
                is_new_price_lower = active_low_price < old_low_price
                # If yes - This is fine to proceed - Successive Discount (3 months to worry later)
                if is_new_price_lower:
                    continue
                else:
                    #any_warnings.append(f"{market} {sku} {rp:2}M rental plan : new low price greater than previous low price : [{active_low_price} vs {old_low_price}]")
					pass

            # If SKU is not currently discounted - check the 30-day low price
            else:
                # We check this even if the discount is allowed because we still need to use the low 30-day price regardless
                col_low_30day = f"min_low_{rp}m"
                # Just in case, not forced to numeric before now...
                try:
                    low_30day = float(lowest_prices[col_low_30day].values[0])
                    # Check the high price against the lowest price
                    is_high_price_lower_than_30day_low = active_high_price <= low_30day
                    if is_high_price_lower_than_30day_low:
                        continue
                    else:
                        any_warnings.append(
                            f"{market} {sku} {rp:2}M rental plan : High price for discount not using the lowest 30-day price : [{active_high_price} vs {low_30day}]"
                        )
                except:
                     #any_warnings.append(f"{market} {sku} {rp:2}M rental plan : Lowest 30-day value is missing.")
                    pass
    # Done with checks - report back
    if any_warnings:
        print_warning("\n".join(any_warnings))
