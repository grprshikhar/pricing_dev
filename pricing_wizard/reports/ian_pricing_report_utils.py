# Ian Connelly, 11 May 2022
#import math

# Function wrapper to pull out discount and original pricing
def calcRelDisc(price):
	# Cast to a string initially
	price = str(price)
	# If no ',' then no discount so relative discount is 0%
	if "," not in price:
		return 0.0
	# Calculate discount applied
	discount, original = price.split(",")
	discount = float(discount)
	original = float(original)
	#
	discount = (1.0 - discount/original)*100
	return discount

def calcDiscount(price):
	# Cast to a string initially
	price = str(price)
	# If no ',' then no discount so relative discount is 0%
	if "," not in price:
		return 1.0
	# Calculate discount applied
	discount, original = price.split(",")
	discount = float(discount)
	original = float(original)
	# 1.0 = Full price, < 1.0 = discount
	discount = discount/original
	return discount

def calcRelDiscBand(price):
	discount = calcRelDisc(price)
	# Define the boundaries
	discount_levels = [0,5,10,15,20,25,30,50,100]
	for l in discount_levels:
		if discount > l:
			continue
		else:
			return l

def getModeRentalPlan(m1_orders,m3_orders,m6_orders,m12_orders,m18_orders,m24_orders):
	orders = {
		"1"  : m1_orders.sum(),
		"3"  : m3_orders.sum(),
		"6"  : m6_orders.sum(),
		"12" : m12_orders.sum(),
		"18" : m18_orders.sum(),
		"24" : m24_orders.sum()
		}
	mode_plan = max(orders, key=lambda key: orders[key])
	return mode_plan

def clean(p):
	if type(p) == str:
		return float(p.split(",")[0])
	else:
		return p

def addDateCalculations(df, rplan, end_date):
	# df       - dataframe : sku with price session date-ordered 
	# rplan    - prefix for rental plan
	# end_date - last date considered

	# Start date of the pricing session
	date_start      = rplan+"_date_start"
	# Diff in days between price session start date and next row
	date_diff       = rplan+"_date_diff"
	# Diff in days between price session start date and last date considered
	date_diff_end   = date_diff+"_end"
	# Number of days price session lasted (identifying cases where price session runs til the last date considered)
	days_in_session = rplan+"_days_in_session"

	# Need to be careful to ensure the data is sorted as expected to extract appropriate days_in_session
	# df = df.sort_values(["store_parent","product_sku",date_start])

	# Verbose 
	# print ("Calculating the length of price sessions")
	# print (f"  Columns ({rplan}) : {date_start}, {date_diff}, {date_diff_end}, {days_in_session}")

	# Evaluate new columns using date information
	# shift(-1) - look at next row
	# Number of days between this row start date and next row
	df[date_diff]     = (df[date_start].shift(-1) - df[date_start]).dt.days
	# I need to have a way to track if the sku changed beyond trusting the date will go negative
	# True here means no change, False means the sku changed in the next row
	df["sku_shift"]   = (df["product_sku"].shift(-1) == df["product_sku"])
	# Number of days between this row start date and last date considered
	df[date_diff_end] = (end_date - df[date_start]).dt.days
	# Clean NaN due to last entry having no variable to shift to
	df[date_diff]     = df[date_diff].fillna(0)

	# Identify length of price session
	# - if date_diff is equal to or longer than 1 day, it means that the next row is a valid date for the SKU
	# - if date_diff is equal to zero it means the next row has the same start date so must be new SKU
	# - if date_diff is -1 it means we moved on from start date at least once in an SKU 
	#   but the next entry is an earlier start date and hence new SKU
	# - if date_diff <= 0 : we should take the value calculate til the end of the data being considered

	# axis=1 needed as we calculate using multiple columns, so need to 'apply' row-wise
	df[days_in_session] = df.apply(lambda x : x[date_diff] if (x[date_diff] >= 1 and x["sku_shift"] == True) else x[date_diff_end], axis=1)
	return df






