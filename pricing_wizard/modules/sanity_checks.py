from tabulate import tabulate
from termcolor import colored,cprint
from modules.print_utils import print_exclaim, print_warning, print_check
from modules.warning_tracker import warning_tracker, warning_object

try:
    import sys
    import colorama
    colorama.init(strip=not sys.stdout.isatty())
except:
    pass

# These are just functions for checking dataframes
def check_dataType(df):
    if df.sku.isnull().values.any() or (~df.sku.str.contains('GR').values).any():
        raise ValueError("SKU column has empty values")
        
    if df.category.isnull().values.any():
        raise ValueError("Category column has empty values")

    if df.subcategory.isnull().values.any():
        raise ValueError("Subcategory column has empty values")

    if df.bulky.isnull().values.any():
        raise ValueError("Bulky column has empty values")

    if not isinstance(df.sku.values[0],str): 
        raise TypeError("SKUs are not string data type! Check input file again.")

    if not isinstance(df.category.values[0],str): 
        raise TypeError("Categories are not string data type! Check input file again.")

    if not isinstance(df.subcategory.values[0],str): 
        raise TypeError("Categories are not string data type! Check input file again.")
        
    if isinstance(df.bulky.values[0],str) or (~df.bulky.isin([0,1]).values).any():
        raise TypeError("Bulky column has incorrect values! Check input file again.")
        
    if isinstance(df.rrp.values[0],str) or (df.rrp==0).values.any() or df.rrp.isnull().values.any(): 
        raise TypeError("RRP is not correctly filled! Check input file again.")
        

def check_discounts(df_td):
    any_errors = []
    
    # Check that a discount present is available on all rental price plans
    # Ian - We now want to allow some plans to have discounts, when others do not, therefore we should not throw and error here
    #     - unless we work out a different logic
    # if df_td[(df_td.comma_count!=df_td.comma_count_plan+1) & (df_td.comma_count>0)].values.any():
    #     SKU = df_td.loc[(df_td.comma_count!=df_td.comma_count_plan+1) & (df_td.comma_count>0),'sku']
    #     any_errors.append("Discount is missing for "+str(SKU.values))

    # We should also validate that the discount amount is less than the full price (ie reprice being entered as discount)
    for plan in [1,3,6,12,18,24]:
        active_plan_name = f"active_plan{plan}"
        high_plan_name   = f"high_plan{plan}"
        # Report if active price is greater than high price for discount
        if df_td[ (df_td[active_plan_name] > df_td[high_plan_name]) ].values.any():
            SKU = df_td.loc[(df_td[active_plan_name] > df_td[high_plan_name]), 'sku'].drop_duplicates()
            any_errors.append(f"{plan}M plan has active price > high price for {SKU.values}")

        # Check if active price equals high price and we have discounts present (check active and high and check if comma in plan)
        if df_td[ (df_td[active_plan_name] == df_td[high_plan_name]) & (df_td[f"plan{plan}"].str.contains(",")) ].values.any():
            SKU = df_td.loc[(df_td[active_plan_name] == df_td[high_plan_name]) & (df_td[f"plan{plan}"].str.contains(",")), 'sku'].drop_duplicates()
            any_errors.append(f"{plan}M plan has active price = high price with a discount format for {SKU.values}")

    if any_errors:
        raise ValueError("\n".join(any_errors))

        
def check_plan_hierarchy(df_td):
    # Warnings
    wt = warning_tracker()
    # Build up errors
    error_list = []
    # Longer plan active values can't be more expensive than shorter
    list_plans = [1,3,6,12,18,24]
    i=0
    for plan in [3,6,12,18,24]:
        ag = list_plans[i]
        i+=1
        pc = "plan"+str(plan)
        agnst = "plan"+str(ag)
        pc_act = "active_plan"+str(plan)
        agnst_act = "active_plan"+str(ag)   
        
        if df_td.loc[(df_td[agnst]!='') & (df_td[pc]!='') & (df_td[agnst_act]<df_td[pc_act])].empty!=True:
            sku = df_td.loc[(df_td[agnst_act]<df_td[pc_act]),'sku']
            error_list.append(str(plan)+"M Plan Price is Expensive than "+str(ag)+"M for "+str(sku.values))
        
        if df_td.loc[(df_td[agnst]!='') & (df_td[pc]!='') & (df_td[agnst_act]==df_td[pc_act])].empty!=True:
            sku = df_td.loc[(df_td[agnst_act]==df_td[pc_act]),'sku']
            for sku_v in sku.values:
                wt.add_warning(warning_object("Equal plans",sku,'','All',str(plan),f"Equal to {ag} plan"))



    # Longer plan high values can't be more expensive than shorter
    i=0
    for plan in [3,6,12,18,24]:
        ag = list_plans[i]
        i+=1
        pc = "plan"+str(plan)
        agnst = "plan"+str(ag)
        pc_act = "high_plan"+str(plan)
        agnst_act = "high_plan"+str(ag) 
        
        if df_td.loc[(df_td[agnst].str.contains(',')) & (df_td[agnst_act]<df_td[pc_act])].empty!=True:
            sku = df_td.loc[(df_td[agnst_act]<df_td[pc_act]),'sku']
            error_list.append(str(plan)+"M Plan High Price is Expensive than "+str(ag)+"M for "+str(sku.values))

        if df_td.loc[(df_td[agnst].str.contains(',')) & (df_td[agnst_act]==df_td[pc_act])].empty!=True:
            sku = df_td.loc[(df_td[agnst_act]==df_td[pc_act]),'sku']
            for sku_v in sku.values:
                wt.add_warning(warning_object("Equal high plans",sku,'','All',str(plan),f"Equal to {ag} plan"))

    # Raise error if exist
    if error_list:
        raise ValueError("\n".join(error_list))
            

### Setting plan wise Hard boundaries in %RRP

'''
CREATE A PLAN BOUNDARY DICTIONARY LIKE:
plan_limit_dict = {
    1 : [0.085,0.5],
    3 : [0.068,0.3],
    6 : [0.055,0.16],
    12 : [0.034,0.078],
    18 : [0.03,0.054],
    24 : [0.025,0.041]
}
'''

def check_rrp_perc(df_td,plan_limit_dict):
    # Singleton warning tracker
    wt = warning_tracker()
    # Print out the options being used
    print_exclaim("Price % guidelines being checked")
    # Convert dict to 100* value for better comprehension when printed out
    plan_limit_dict_print = {k: [100*x for x in v] for k, v in plan_limit_dict.items()}
    # print(colored(tabulate(plan_limit_dict_print,
    #             headers=[str(x)+"M" for x in plan_limit_dict_print.keys()],
    #             showindex=["min %","max %"], tablefmt="psql"),attrs=["reverse"]))
    # print("")
    # Error tracker
    any_warnings = []
    for k, dk in plan_limit_dict.items():
        act_pp = "act_perc_pp_"+str(k)
        low_limit = dk[0] 
        high_limit = dk[1]
        if df_td.loc[(df_td[act_pp]<=low_limit)].empty!=True:
            sku = df_td.loc[(df_td[act_pp]<=low_limit),['store code','sku',act_pp]]
            any_warnings.append( str(k)+"M Plan Price is too cheap for SKUs \n"+ "\n".join([str(x) for x in sku.values]) )
            for x in sku.values:
                wt.add_warning(warning_object('RRP %',x[1],'',x[0],k,f'Price is too cheap (< {low_limit})'))
        
        if df_td.loc[(df_td[act_pp]>=high_limit)].empty!=True:
            sku = df_td.loc[(df_td[act_pp]>=high_limit),['store code','sku',act_pp]]
            any_warnings.append( str(k)+"M Plan Price is too expensive for SKUs \n"+ "\n".join([str(x) for x in sku.values]) )
            for x in sku.values:
                wt.add_warning(warning_object('RRP %',x[1],'',x[0],k,f'Price is too expensive (> {high_limit})'))

    # Track all cases of RRP issues to better inform the user
    if any_warnings:
        print_warning("\n".join(any_warnings))

def last_digit_9 (df_td):
    wt = warning_tracker()
    # Error tracker
    any_warnings = []
    for plan in [1,3,6,12,18,24]:
        pc = "active_plan"+str(plan)
        if df_td.loc[(df_td[pc]*10%10<9) | (df_td[pc]*10%10>9)].empty!=True:
            sku = df_td.loc[(df_td[pc]*10%10<9) | (df_td[pc]*10%10>9),'sku'].drop_duplicates()
            any_warnings.append( str(plan)+"M Plan has non Charm prices for SKUs : "+str(sku.values) )
            for x in sku.values:
                wt.add_warning(warning_object('Charm prices',x,'',None,plan,'Missing charm pricing ending in XX.9'))

    # Track all cases of charm pricing not used to better inform the user
    if any_warnings:
        print_warning("\n".join(any_warnings))

def check_minimum(df_td, minval):
    wt = warning_tracker()
    any_warnings = []
    for plan in [1,3,6,12,18,24]:
        pc = "active_plan"+str(plan)
        if df_td.loc[(df_td[pc]<minval)].empty != True:
           sku = df_td.loc[(df_td[pc]<minval), 'sku'].drop_duplicates()
           any_warnings.append( str(plan) + f"M Plan has low price (below {minval}€ or {minval}$) : " + str(sku.values) )
           for x in sku.values:
                wt.add_warning(warning_object('Minimum price',x,'',None,plan,f'Low price is below minimum value (< {minval})'))
    if any_warnings:
        print_warning("\n".join(any_warnings))

# Check the price change tag is provided
def check_price_change_tag(df):
    wt = warning_tracker()
    any_warnings = []
    if df.loc[(df['price change tag'] == "")].empty != True:
        sku = df.loc[(df['price change tag'] == ""), 'sku'].drop_duplicates()
        for s in sku:
            any_warnings.append(f"{s} : No price change tag provided")
            wt.add_warning(warning_object('Price change tag',s,'',None,None,'Missing price change tag'))
    if any_warnings:
        print_warning("\n".join(any_warnings))

def check_margin_columns(df):
    wt = warning_tracker()
    any_warnings = []
    required_cols = ['m1_margin', 'm3_margin', 'm6_margin', 'm12_margin', 'm18_margin', 'm24_margin', 'combined_margin']
    for col in required_cols:
        if col not in df.columns:
            any_warnings.append(f"{col} : Margin Columns are missing please add Margin columns (MATRIX sheet CQ -> CW) to the export tab ")
            wt.add_warning(warning_object('Margin columns',None,'',None,None,f'Missing margin column ({col})'))
    if any_warnings:
        print_warning("\n".join(any_warnings))
        return False
    else:
        return True




# For now, if we have a bulky item, our 1M rental should generate same profit as 3M
#def bulky_plan_check(df):
#    any_warnings = []
    # Comparing active price because high price not defined when repricing (but does mean discounts might flag this)
#    bulky   = "bulky"
#    high_1M = "active_plan1"
#    high_3M = "active_plan3"
#    if df.loc[(df[high_1M] < 3.0*df[high_3M]) & (df[bulky] == 1)].empty != True:
#        sku = df.loc[(df[high_1M] < 3.0*df[high_3M]) & (df[bulky] == 1), "sku"].drop_duplicates()
#        for s in sku:
#            any_warnings.append(f"Bulky sku [{s}] : 1M  < (3 * 3M) high price, required due to increased shipping costs")
#    if any_warnings:
#        print_warning("\n".join(any_warnings))



            

#### Summarize data

def show_summary(df_td):
    desc_prices = df_td.describe(exclude=['object','int'])
    print("")
    cprint("$$  Total Price Uploads - "+str(len(df_td))+"  $$",'white','on_blue', attrs=['bold','blink'])
    print(colored("\n\n>>## Total Bulky Items - ",'green'),colored(str(sum(df_td.bulky)),'yellow')+"\n")  
    print(colored(">>$$ Total RRP > 2000 Items - ",'green'),colored(str((df_td.rrp>2000).count()),'yellow')+"\n\n")  
    a=df_td['duration_plan'].value_counts().rename_axis('Plans').reset_index(name='Price uploads')
    print(colored("Number of uploads per plan\n",'green')+colored(tabulate(a, headers='keys', tablefmt='psql'),'yellow')+"\n")

    a=df_td['store code'].value_counts().rename_axis('Store Codes').reset_index(name='Price uploads')
    print(colored("Number of uploads for each store\n",'green')+colored(tabulate(a, headers='keys', tablefmt='psql'),'yellow')+"\n")

    a=df_td['subcategory'].value_counts().rename_axis('Subcategory').reset_index(name='Price uploads')
    print(colored("Number of uploads for each Subcategory\n",'green')+colored(tabulate(a, headers='keys', tablefmt='psql'),'yellow')+"\n")

    pivot = df_td[['sku','store code']].pivot_table( index='sku', values='store code', columns='store code', aggfunc=len, fill_value=0, dropna=False)
    print(colored("SKU / Market breakdown","green"))
    print(colored(tabulate(pivot, headers='keys', tablefmt='psql'),'yellow')+"\n\n")

def show_stats(df_td):
    desc_prices = df_td.describe(exclude=['object','int'])
    print("")
    pp_dt = desc_prices[[col for col in desc_prices.columns if 'act_perc_pp' in col]]
    pp_dt.columns = pp_dt.columns.str.replace("act_perc_pp_", "Act PP % ")
    print(colored("New Active PP Percentage data summary\n",'green')+colored(tabulate(pp_dt, headers='keys', tablefmt='psql'),'yellow')+"\n")
    acti_dt = desc_prices[[col for col in desc_prices.columns if 'acti' in col]]
    acti_dt.columns = acti_dt.columns.str.replace("active_plan", "Active Plan ")
    print(colored("New Active Price data summary\n",'green')+colored(tabulate(acti_dt, headers='keys', tablefmt='psql'),'yellow')+"\n")
    high_dt = desc_prices[[col for col in desc_prices.columns if 'high_plan' in col]]
    high_dt.columns = high_dt.columns.str.replace("high_plan", "High Plan ")
    print(colored("New High Price data summary\n",'green')+colored(tabulate(high_dt, headers='keys', tablefmt='psql'),'yellow')+"\n")    
    disc_dt = desc_prices[[col for col in desc_prices.columns if 'disc' in col]]
    print(colored("Discount data summary\n",'green')+colored(tabulate(disc_dt, headers='keys', tablefmt='psql'),'yellow')+"\n")   




