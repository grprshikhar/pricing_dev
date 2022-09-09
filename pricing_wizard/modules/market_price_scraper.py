def market_price_scraper():
    # Imports
    from sklearn.ensemble import IsolationForest
    import pandas as pd
    import numpy as np
    from statistics import mean
    from datetime import datetime
    import json
    import requests
    import scipy.stats as stats
    import sqlite3 
    from modules.gdrive import download_pricsync, upload_pricsync
    from modules.print_utils import print_check, print_exclaim, tabulate_dataframe, print_exclaim_sameline
    from modules.gsheet import upload_df_to_gsheet

    # Date
    date_today =datetime.today().strftime('%Y-%m-%d')

    # Check if the database is already updated
    database_filename = 'competition_pricing.db'
    print_exclaim(f"Downloading database [{database_filename}] from gdrive")
    download_pricsync(database_filename)

    # Make a connection
    conn = sqlite3.connect(database_filename)
    last_run = pd.read_sql_query('SELECT crawl_date FROM data_output ORDER BY crawl_date DESC limit 1',conn)
    last_run_date = last_run["crawl_date"].loc[0]
    if last_run_date == date_today:
      print_check("Database already contains price data for today")
      print_exclaim("Updating spreadsheet with latest data")
      output = pd.read_sql_query(f'SELECT * FROM data_output where crawl_date="{date_today}"',conn)
      response = upload_df_to_gsheet(output.drop(columns='index'))
      print_check(response)
      return
    else:
      print_check(f"Competition prices last scraped on: {last_run_date}")

    conn.close()

    print_exclaim("Downloading data from API Link (Please be patient...)")
    Start_Url = 'https://prisync.com/api/v2/list/product/summary/startFrom/0'
    params = {'apikey': 'Grover-DE@prisync.com',
                'apitoken': 'e50e8ed3f27a5a24c7ba03297eedf643'}
    response = requests.get(Start_Url,headers = params)
    json_data = json.loads(response.text)

    # Extracting All the Data from the API links
    def get_data(url, dataframe, params):
      print_exclaim_sameline(f"Processing {url}...")
      
      response = requests.get(url, headers = params)
      json_data = json.loads(response.text)
      df = pd.DataFrame.from_dict(pd.json_normalize(json_data['results']))
      
      dataframe = pd.concat([dataframe, df])
      if not json_data["nextURL"]:
        return dataframe
      nextUrl = "https://prisync.com" + json_data["nextURL"]
      return get_data(nextUrl, dataframe, params)
      
    df = pd.DataFrame()
    dataframe = get_data(Start_Url, df, params)

    # Clean up the line
    print_exclaim_sameline("\n")
    print_check("Data downloaded from API Link")


    """#### Cleaning the data:"""
    print_exclaim("Cleaning data downloaded")
    x2 = dataframe.set_index(['id', 'name', 'product_code', 'barcode', 'cost', 'tags', 'brand.id','brand.name', 'category.id', 'category.name'])
    x2 = x2.rename_axis((['website']), axis=1).stack(-1).reset_index()
    #splitting the first word from the string "summary"
    x2['website_names'] = x2['website'].str.split('.').str[1] 
    #splitting the last word from the string "stock" or "price"
    x2['criteria'] = x2['website'].str.extract('([^.]+)$', expand=False) 
    x2['link'] = x2['website'].apply(lambda x: x.split('.',1)[1]) 
    # getting the link only
    x2['link_only'] = x2['link'].apply(lambda x: x.rsplit('.',1)[-2])  
    #dropping not needed columns 
    x2.drop(columns=['website', 'link', 'website_names'], inplace = True, axis = 1) 
    #copying data in column 0 to a new column named values
    x2["values"] = x2.iloc[ : ,  10] 
    # reseting index for assurance only
    x2 = x2.reset_index()   
    # dropping column named 0
    x2.drop(x2.columns[[11]],axis = 1, inplace=True) 

    def func(x):
      return x.values[-1]
    #categorising stock and price columns and taking the corresponding value to it
    x3 = x2.pivot_table(index=['id', 'name', 'product_code', 'barcode', 'cost', 'tags', 'brand.id','brand.name', 'category.id', 'category.name', 'link_only'], columns='criteria', values="values", aggfunc= func ) 
    # reseting index to get the indexed column names duplicated for all websites
    x3 = x3.reset_index()  
    # Output should be results for next section
    results = x3.copy(deep = True)
    results.rename(columns = {'brand.name' : "brand_name", 'cost':'inhouse_RRP'}, inplace = True)
    print_check("Data cleaned")


    """## Removing anomalous pricing points with IsolationForest """
    print_exclaim("Running IsolationForest")
    def fit_model(model, data, column='price'):
        # fit the model and predict it
        df = data.copy()
        data_to_predict = data[column].to_numpy().reshape(-1, 1)
        predictions = model.fit_predict(data_to_predict)
        df['Predictions'] = predictions
        
        return df

    results = results[results['stock']==True]
    # Isolation forest will work for each distinct id

    unique_ids = []
    unique_ids= results["product_code"].unique()
    x = unique_ids


    final_df = pd.DataFrame(columns=['id', 'name', 'product_code', 'barcode', 'cost', 'tags', 'brand.id',
            'brand.name', 'category.id', 'category.name', 'link_only', 'price',
            'stock', 'Predictions'])

    for prod_code in unique_ids:
      iso_forest = IsolationForest(n_estimators=50, contamination=0.25)
      iso_df = fit_model(iso_forest, results[results['product_code']==prod_code])
      iso_df['Predictions'] = iso_df['Predictions'].map(lambda x: 1 if x==-1 else 0)
      final_df = pd.concat([final_df, iso_df], ignore_index=True)

    final_df_wo_outliers = final_df[final_df['Predictions']==0]

    final_df_wo_outliers.head()

    results_reduced = final_df_wo_outliers.copy(deep = True)


    print_check("IsolationForest complete")


    """## Identifying frequency of websites per category"""
    print_exclaim("Identifying frequency of websites per category")

    category_site_frequency = results_reduced.groupby('category.name')['link_only'].value_counts().unstack().fillna(0)
    category_site_frequency.index.names = [None]
    category_site_frequency = category_site_frequency.transpose()
    category_site_frequency = category_site_frequency.reset_index() 
    category_site_frequency.head()

    """### Sorting Top 10 websites in each category """

    Audio_sorted = category_site_frequency.sort_values(by = 'Audio & Music', ascending=False)
    Audio_sites = Audio_sorted["link_only"].iloc[:10]
    #Audio_sites
    Cameras_sorted = category_site_frequency.sort_values(by = 'Cameras', ascending=False)
    Cameras_sites = Cameras_sorted["link_only"].iloc[:10]
    #Cameras_sites
    Computers_sorted = category_site_frequency.sort_values(by = 'Computers', ascending=False)
    Computers_sites = Computers_sorted["link_only"].iloc[:10]
    #Computers_sites
    Drones_sorted = category_site_frequency.sort_values(by = 'Drones', ascending=False)
    Drones_sites = Drones_sorted["link_only"].iloc[:10]
    #Drones_sites
    Fitness_sorted = category_site_frequency.sort_values(by = 'Fitness', ascending=False)
    Fitness_sites = Fitness_sorted["link_only"].iloc[:10]
    #Fitness_sites
    Gaming_sorted = category_site_frequency.sort_values(by = 'Gaming & VR', ascending=False)
    Gaming_sites = Gaming_sorted["link_only"].iloc[:10]
    #Gaming_sites
    Home_entertainment_sorted = category_site_frequency.sort_values(by = 'Home Entertainment', ascending=False)
    Home_entertainment_sites = Home_entertainment_sorted["link_only"].iloc[:10]
    #Home_entertainment_sites
    Phones_sorted = category_site_frequency.sort_values(by = 'Phones & Tablets', ascending=False)
    Phones_sites = Phones_sorted["link_only"].iloc[:10]
    #Phones_sites
    Smart_home_sorted = category_site_frequency.sort_values(by = 'Smart Home', ascending=False)
    Smart_home_sites = Smart_home_sorted["link_only"].iloc[:10]
    #Smart_home_sites
    Wearables_sorted = category_site_frequency.sort_values(by = 'Wearables', ascending=False)
    Wearables_sites = Wearables_sorted["link_only"].iloc[:10]
    #Wearables_sites
    eMobility_sorted = category_site_frequency.sort_values(by = 'eMobility', ascending=False)
    eMobility_sites = eMobility_sorted["link_only"].iloc[:10]
    #eMobility_sites

    Audio_sites_freq = Audio_sorted[['link_only', 'Audio & Music']]
    Cameras_sites_freq = Cameras_sorted[['link_only', 'Cameras']]
    Drones_sites_freq = Drones_sorted[['link_only', 'Drones']]
    Computers_sites_freq = Computers_sorted[['link_only', 'Computers']]
    Fitness_sites_freq = Fitness_sorted[['link_only', 'Fitness']]
    Gaming_sites_freq = Gaming_sorted[['link_only', 'Gaming & VR']]
    Home_entertainment_sites_freq = Home_entertainment_sorted[['link_only', 'Home Entertainment']]
    Phones_sites_freq = Phones_sorted[['link_only', 'Phones & Tablets']]
    Smart_home_sites_freq = Smart_home_sorted[['link_only', 'Smart Home']]
    Wearables_sites_freq = Wearables_sorted[['link_only', 'Wearables']]
    eMobility_sites_freq = eMobility_sorted[['link_only', 'eMobility']]
    print_check("Websites frequencies identified")

    """## Collecting key price points"""
    print_exclaim("Collecting key price points")

    sites = {
    "Audio & Music" : Audio_sites,
    "Cameras" : Cameras_sites,
    "Computers" : Computers_sites,
    "Drones" : Drones_sites,
    "Fitness" : Fitness_sites,
    "Gaming & VR" : Gaming_sites,
    "Home Entertainment" : Home_entertainment_sites,
    "Phones & Tablets" : Phones_sites,
    "Smart Home" : Smart_home_sites,
    "Wearables" : Wearables_sites,
    "eMobility" : eMobility_sites,
    }


    grouped_results_reduced = results_reduced.groupby(["product_code","category.name"])

    final_df = pd.DataFrame(columns=['sku','Trusted_sites_price','Overall_median_price', 'Overall_mean_price', 'number_trusted_sites', 'number_sites'])

    for name, group in grouped_results_reduced:
      sku = name[0]
      cat = name[1]
      sites_to_use = sites[cat]
      SKU_median = group["price"].median()
      group["price"] = group["price"].astype(float)
      SKU_mean = group["price"].mean()
      new_group = group[group["link_only"].isin(sites_to_use)]
      gg_df = pd.DataFrame(new_group)
      test = gg_df["price"].astype(float).mean()
      number_sites = len(group)
      number_trusted_sites = len(new_group)
      temp_df = pd.DataFrame(data={'sku':[sku], 'Trusted_sites_price':[test], 'Overall_median_price':[SKU_median], "Overall_mean_price": [SKU_mean], "number_sites" :[number_sites], "number_trusted_sites" :[number_trusted_sites]})
      final_df = pd.concat([final_df, temp_df], ignore_index=True)
      
    sku_prices = final_df.copy(deep = True)

    print_check("Key price points collected")


    """## Final ideal prices"""
    print_exclaim("Calculating final price column")


    def percentage_change(col1,col2):
      try:
        z = ((np.abs(col2 - col1)) / col1) * 100
      except:
        z = 0 
      return z

    Last_df = pd.DataFrame()
    Last_df = pd.merge(sku_prices, results_reduced, right_on = "product_code" , left_on ="sku" ,how='left')
    Last_df['percentage_change'] = percentage_change(Last_df['Overall_mean_price'],Last_df['Trusted_sites_price'])
    Last_df['final_price'] = np.where(Last_df['percentage_change']>=10, Last_df['Trusted_sites_price'], Last_df['Overall_mean_price'])
    Last_df.drop(columns=['id','barcode','brand.id','category.id','tags'], inplace = True, axis = 1)
    Last_df = Last_df.merge(results_reduced[["name", "brand.name", "category.name", "product_code", "stock"]], how = 'left', on = "product_code")
    Last_df = Last_df.drop_duplicates()
    

    print_check("Calculated final price column")


    Last_df = Last_df.drop(['name_y', 'brand.name_y', 'category.name_y','stock_y','link_only','product_code'], axis =1)
    Last_df = Last_df.drop_duplicates(subset=['sku'], keep='first')

    # creating a column for brand price
    
    results["Compare"] =  [x[0].lower() in x[1].lower() for x in zip(results['brand_name'], results['link_only'])]
    brands_df = results[results.Compare != False]
    brands_df_prices = brands_df[['product_code','price']].copy()
    brands_df_prices.rename(columns = {'price':'brand_price'}, inplace = True) 
    Last_df = Last_df.merge(brands_df_prices, how = 'left' ,left_on = 'sku', right_on = "product_code")
    Last_df.drop(['brand.name_x', 'Predictions'], inplace = True, axis = 1)
    Last_df.rename(columns = {'name_x':'product_name', 'category.name_x': 'category_name', 'cost':'inhouse_RRP'}, inplace = True)
    
    # creating a column for Amazon Prices
    
    results["Amazon_prices"] = results['link_only'].str.contains('amazon')
    Amazon_prices = results[results.Amazon_prices != False]
    Amazon_prices_df = Amazon_prices[['product_code','price']].copy()
    Amazon_prices_df.rename(columns = {'price':'Amazon_prices'}, inplace = True) 
    Last_df = Last_df.merge(Amazon_prices_df, how = 'left' ,left_on = 'sku', right_on = "product_code")
    Last_df.drop(["product_code_x", "product_code_y"], inplace = True, axis = 1)
    
    # creating a column for Mediamarkt Prices
    
    results["Mediamarkt_prices"] = results['link_only'].str.contains('mediamarkt')
    Mediamarkt_prices = results[results.Mediamarkt_prices != False]
    Mediamarkt_prices_df = Mediamarkt_prices[['product_code','price']].copy()
    Mediamarkt_prices_df.rename(columns = {'price':'Mediamarkt_prices'}, inplace = True) 
    Last_df = Last_df.merge(Mediamarkt_prices_df, how = 'left' ,left_on = 'sku', right_on = "product_code")
    Last_df.drop(["product_code","price"], inplace = True, axis = 1)
    Last_df['crawl_date'] = date_today

    # Checking data
    tabulate_dataframe(Last_df.tail())

    # Working on sqlite database  
    print_exclaim("Updating local database with new data")
    conn = sqlite3.connect(database_filename)
    output = Last_df.applymap(str)
    output.to_sql(name='data_output', con=conn, if_exists = 'append')
    conn.commit()

    # Run a check
    new_df2 = pd.read_sql_query('SELECT * FROM data_output',conn)
    tabulate_dataframe(new_df2.tail())
    conn.close()
    print_check("Local database updated")

    # Check for duplicate rows
    if new_df2[new_df2.duplicated()].empty != True:
      print_exclaim("Duplicate rows identified in dataframe.")
      print_exclaim("Please check")
      tabulate_dataframe(new_df2[new_df2.duplicated()])
    
    # Update google drive with new database
    print_exclaim("Updating database in gdrive")
    upload_pricsync(database_filename)
    print_check("Database updated in gdrive")

    # Updating gsheet
    print_exclaim("Updating spreadsheet with latest data")
    response = upload_df_to_gsheet(Last_df)
    print_check(response)
    print_check("Spreadsheet update complete")






