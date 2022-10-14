def market_price_scraper_v02_US():
  # Imports
  import modules.gsheet as gsheet
  from sklearn.ensemble import IsolationForest
  import pandas as pd
  import numpy as np
  from statistics import mean
  from datetime import datetime
  import json
  import requests
  import scipy.stats as stats
  import sqlite3 
  from modules.gdrive import download_pricsync_US, upload_pricsync_US
  from modules.print_utils import print_check, print_exclaim, tabulate_dataframe, print_exclaim_sameline
  from modules.gsheet import upload_df_to_gsheet_US
  #from modules.gsheet import gdrive
  from scipy.stats import gmean


  # Date
  date_today =datetime.today().strftime('%Y-%m-%d')

  print_exclaim("Updating Competition Pricing for US")

  # Check if the database is already updated
  database_filename = 'competition_pricing_v02_US.db'
  print_exclaim(f"Downloading database [{database_filename}] from gdrive")
  download_pricsync_US(database_filename)

  # Make a connection
  conn = sqlite3.connect(database_filename)
  last_run = pd.read_sql_query('SELECT crawl_date FROM data_output ORDER BY crawl_date DESC limit 1',conn)
  last_run_date = last_run["crawl_date"].loc[0]
  if last_run_date == date_today:
    print_check("Database already contains price data for today")
    print_exclaim("Updating spreadsheet with latest data")
    output = pd.read_sql_query(f'SELECT * FROM data_output where crawl_date="{date_today}"',conn)
    #print (output.dtypes)
    response = upload_df_to_gsheet_US(output.drop(columns='index'))
    #print_check(response)
    return
  else:
    print_check(f"Competition prices last scraped on: {last_run_date}")

  conn.close()


  print_exclaim("Downloading data from API Link (Please be patient...)")
  Start_Url = 'https://prisync.com/api/v2/list/product/summary/startFrom/0'
  params = {'apikey': 'Grover-USA@prisync.com',
              'apitoken': '4fe53a62de572aeb1453b4e6ab7c0b47'}
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
  results.rename(columns = {'brand.name' : "brand_name"}, inplace = True)
  print_check("Data cleaned")

  # Adding inhouse Market Price to the results 
  print_exclaim("Adding inhouse Market Price to the results")
  inhouse_market_prices = gsheet.get_dataframe("13fvWqCqV1cgt6vrpg5INJzX0haBx2znwwt5VM_30j0A","US Market Price!A:B","Market Price")
  inhouse_market_prices["market price"]  = inhouse_market_prices["market price"].apply(pd.to_numeric, errors='coerce')
  inhouse_market_prices = inhouse_market_prices[inhouse_market_prices['market price'].notna()]
  inhouse_market_prices = inhouse_market_prices.rename(columns  = {"market price":"Inhouse_Market_Price"})
  #print(inhouse_market_prices)

  # Merging the inhouse Market prices to the main df

  results = pd.merge(results, inhouse_market_prices, left_on = "product_code", right_on = "product code", how = "left")
  results = results.drop(['product code', 'cost', 'barcode', 'brand.id', 'category.id','id','tags'], axis=1)


  # Importing the Catmans websites ranking for each category
  print_exclaim("Importing the Catmans websites ranking for each category")


  audio_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","Audio!A:C","Catman Trust (condition New)")
  audio_sites = audio_sites[["link_only","catman trust (condition new)"]].copy()
  audio_sites = audio_sites.replace(r'^\s*$', 1, regex=True)
  

  cameras_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","Cameras!A:C","Catman Trust (condition New)")
  cameras_sites = cameras_sites[["link_only","catman trust (condition new)"]].copy()
  cameras_sites = cameras_sites.replace(r'^\s*$', 1, regex=True)


  drones_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","Drones!A:C","Catman Trust (condition New)")
  drones_sites = drones_sites[["link_only","catman trust (condition new)"]].copy()
  drones_sites = drones_sites.replace(r'^\s*$', 1, regex=True)


  computers_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","Computers!A:C","Catman Trust (condition New)")
  computers_sites = computers_sites[["link_only","catman trust (condition new)"]].copy()
  computers_sites = computers_sites.replace(r'^\s*$', 1, regex=True)


  fitness_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","Fitness!A:C","Catman Trust (condition New)")
  fitness_sites = fitness_sites[["link_only","catman trust (condition new)"]].copy()
  fitness_sites = fitness_sites.replace(r'^\s*$', 1, regex=True)



  gaming_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","Gaming!A:C","Catman Trust (condition New)")
  gaming_sites = gaming_sites[["link_only","catman trust (condition new)"]].copy()
  gaming_sites = gaming_sites.replace(r'^\s*$', 1, regex=True)


  home_entertainment_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","Home_entertainment!A:C","Catman Trust (condition New)")
  home_entertainment_sites = home_entertainment_sites[["link_only","catman trust (condition new)"]].copy()
  home_entertainment_sites = home_entertainment_sites.replace(r'^\s*$', 1, regex=True)


  phones_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","Phones_Tablets!A:C","Catman Trust (condition New)")
  phones_sites = phones_sites[["link_only","catman trust (condition new)"]].copy()
  phones_sites = phones_sites.replace(r'^\s*$', 1, regex=True)



  smart_home_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","Smart_Home!A:C","Catman Trust (condition New)")
  smart_home_sites = smart_home_sites[["link_only","catman trust (condition new)"]].copy()
  smart_home_sites = smart_home_sites.replace(r'^\s*$', 1, regex=True)


  wearables_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","Wearables!A:C","Catman Trust (condition New)")
  wearables_sites = wearables_sites[["link_only","catman trust (condition new)"]].copy()
  wearables_sites = wearables_sites.replace(r'^\s*$', 1, regex=True)


  emobility_sites = gsheet.get_dataframe("1v-5C8xjdsgnegSEly-ZO8xfoHlHb5-JHmrVWoVbRvUw","eMobility!A:C","Catman Trust (condition New)")
  emobility_sites = emobility_sites[["link_only","catman trust (condition new)"]].copy()
  emobility_sites = emobility_sites.replace(r'^\s*$', 1, regex=True)


  results_audio = results[results["category.name"] == "Audio & Music"]
  results_camera = results[results["category.name"] == "Cameras"]
  results_drones = results[results["category.name"] == "Drones"]
  results_computers = results[results["category.name"] == "Computers"]
  results_fitness = results[results["category.name"] == "Fitness"]
  results_gaming = results[results["category.name"] == "Gaming & VR"]
  results_home_entertainment = results[results["category.name"] == "Home Entertainment"]
  results_phones = results[results["category.name"] == "Phones & Tablets"]
  results_smart_home = results[results["category.name"] == "Smart Home"]
  results_wearables = results[results["category.name"] == "Wearables"]
  results_emobility = results[results["category.name"] == "eMobility"]

# Merging ranks with their categories
  results_audio = pd.merge(results_audio, audio_sites, on = "link_only", how = "left")
  results_camera = pd.merge(results_camera, cameras_sites, on = "link_only", how = "left")
  results_drones = pd.merge(results_drones, drones_sites, on = "link_only", how = "left")
  results_computers = pd.merge(results_computers, computers_sites, on = "link_only", how = "left")
  results_fitness = pd.merge(results_fitness, fitness_sites, on = "link_only", how = "left")
  results_gaming = pd.merge(results_gaming, gaming_sites, on = "link_only", how = "left")
  results_home_entertainment = pd.merge(results_home_entertainment, home_entertainment_sites, on = "link_only", how = "left")
  results_phones = pd.merge(results_phones, phones_sites, on = "link_only", how = "left")
  results_smart_home = pd.merge(results_smart_home, smart_home_sites, on = "link_only", how = "left")
  results_wearables = pd.merge(results_wearables, wearables_sites, on = "link_only", how = "left")
  results_emobility = pd.merge(results_emobility, emobility_sites, on = "link_only", how = "left")

  # Combining all results in one df with their ranks
  pdList = [results_audio, results_camera, results_drones, results_computers, results_fitness, results_gaming, results_home_entertainment, results_phones, results_smart_home, results_wearables, results_emobility ]  # List of your dataframes
  results_rank = pd.concat(pdList)
  """ Removing anomalous pricing points with IsolationForest """
  print_exclaim("Running IsolationForest")
  
  def fit_model(model, data, column='price'):
    # fit the model and predict it
    df = data.copy()
    data_to_predict = data[column].to_numpy().reshape(-1, 1)
    predictions = model.fit_predict(data_to_predict)
    df['Predictions'] = predictions
    return df

  results = results_rank[results_rank['stock']==True]
  # Isolation forest will work for each distinct id

  unique_ids = []
  x = [unique_ids.append(i) for i in results['product_code'].unique()]


  final_df = pd.DataFrame(columns=['id', 'name', 'product_code', 'barcode', 'cost', 'tags', 'brand.id',
          'brand.name', 'category.id', 'category.name', 'link_only', 'price',
          'stock', 'Predictions'])

  for prod_code in unique_ids:
    iso_forest = IsolationForest(n_estimators=50, contamination=0.25)
    iso_df = fit_model(iso_forest, results[results['product_code']==prod_code])
    iso_df['Predictions'] = iso_df['Predictions'].map(lambda x: 1 if x==-1 else 0)
    final_df = pd.concat([final_df, iso_df], ignore_index=True)

  final_df_wo_outliers = final_df[final_df['Predictions']==0]

  #final_df_wo_outliers.head()

  results_reduced = final_df_wo_outliers.copy(deep = True)
  #print(results_reduced.info())
  print_check("IsolationForest complete")
  """Collecting key price points"""
  print_check("Collecting key price points")
  '''
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
  '''

  grouped_results_reduced = results_reduced.groupby(["product_code","category.name"])

  final_df = pd.DataFrame(columns=['sku','Overall_median_price', 'Overall_mean_price', 'number_sites'])

  for name, group in grouped_results_reduced:
    sku = name[0]
    cat = name[1]
    group["price"] = group["price"].astype(float)
    SKU_median = group["price"].median()
    SKU_mean = group["price"].mean()
    number_sites = len(group)
    final_df = final_df.append({'sku':sku, 'Overall_median_price':SKU_median, "Overall_mean_price": SKU_mean, "number_sites" :number_sites}, ignore_index = True)

  sku_prices = final_df.copy(deep = True)

  results_reduced["price"] = results_reduced["price"].astype(float)
  results_reduced["catman trust (condition new)"].fillna(1, inplace=True)
  results_reduced["catman trust (condition new)"] = results_reduced["catman trust (condition new)"].astype(int)
  SKU_rank_score = results_reduced.groupby("product_code").agg({"catman trust (condition new)":"sum"})
  SKU_rank_score = SKU_rank_score.reset_index()
# Applying weighted average to the results
  
  print_check("Calculating weighted average")
  
  # function to calculate the weighted average
  def weighted_average(df, values, weights):
      return sum(df[weights] * df[values]) / df[weights].sum()

  results_wavg = results_reduced[results_reduced["price"] > 0] 
  results_wavg = results_reduced.groupby('product_code').apply(weighted_average, 'price', 'catman trust (condition new)')
  results_wavg = results_wavg.reset_index()
  results_weighted = pd.DataFrame(columns=['product_code','wavg price'])
  results_weighted["wavg price"] = results_wavg.iloc[ : ,  1] 
  results_weighted["product_code"] = results_wavg.iloc[ : ,  0] 

# Applying Geometric mean to the results:
  print_check("Calculating GMean")
  gmean_df = results_reduced[["product_code","price"]].copy()
  gmean_df = gmean_df[gmean_df['price'] > 0]
  results_gmean = gmean_df.groupby(gmean_df.product_code).apply(stats.gmean)
  results_gmean = pd.DataFrame(data = results_gmean, columns=['price'])
  results_gmean = results_gmean.reset_index()
  results_gmean.rename(columns = {"price":"gmean_price"}, inplace = True)
  results_gmean['gmean_price'] = results_gmean['gmean_price'].astype(float).round(2)

# Final Dataframe

  last_df = sku_prices.copy()
  last_df = pd.merge(last_df, SKU_rank_score, left_on = 'sku', right_on = 'product_code', how = 'left')
  last_df = pd.merge(last_df, results_weighted, on = "product_code", how = 'left')
  last_df = pd.merge(last_df, results_gmean, on = "product_code", how = 'left')
  last_df = pd.merge(last_df, results_reduced[['product_code', 'name', 'brand_name', 'category.name', 'Inhouse_Market_Price']], on = 'product_code', how = 'left')
  last_df = last_df.drop_duplicates()
  last_df = last_df[['product_code', 'name', 'brand_name','category.name', 'Inhouse_Market_Price', 'number_sites', 'catman trust (condition new)', 'Overall_median_price', 'Overall_mean_price', 'wavg price', 'gmean_price']].copy()

  # Adding reliability score for each SKU
  print_check("Calculating Reliability Score")


  cats_mean = results_reduced.groupby("category.name")["catman trust (condition new)"].mean()
  cats_mean = cats_mean.reset_index()
  cats_mean.rename(columns = {'catman trust (condition new)':'Category Mean Rank'}, inplace = True)
  last_df = pd.merge(last_df, cats_mean, on = "category.name", how = "left" )
  last_df["reliability_score"] = last_df["catman trust (condition new)"] / last_df["Category Mean Rank"]
  last_df["reliability_score"] = last_df["reliability_score"].round(2)
  last_df = last_df[['product_code', 'name', 'brand_name','category.name', 'Inhouse_Market_Price', 'number_sites', 'catman trust (condition new)', 'Category Mean Rank', 'reliability_score','Overall_median_price', 'Overall_mean_price', 'wavg price', 'gmean_price']].copy()

  #Adding the quartiles method
  print_check("Calculating Price Quantiles")

  duplicated_df = results_reduced.loc[results_reduced.index.repeat(results_reduced['catman trust (condition new)'])]
  duplicated_df['crawl_date'] = date_today
  duplicated_df = duplicated_df[duplicated_df['price'] > 0]
  #getting all unique SKUs
  prod = duplicated_df['name'].unique() 
  #creating a list of all unique SKUs to use in the for loop below
  products = prod.tolist() 


  output_list = []
  for p in products:
    subset = duplicated_df[duplicated_df['name'] == p]
    subset_2 = results_reduced[results_reduced['name']==p]
    l_org = len(subset_2)
    price = subset['price']
    sku = subset['product_code'].iloc[0]
    crawl_date = subset['crawl_date'].iloc[0]
    market = subset['Inhouse_Market_Price']        
    mar = mean(market)                                
    l=len(price)                                
    m=price.median()
    try:                            
      mode = statistics.mode(price)    
    except:
      mode=m                                  
    quan=[min(price),price.quantile(0.25),price.quantile(0.50),price.quantile(0.75),max(price)]  
    a = abs(quan[0]-quan[1])
    b = abs(quan[1]-quan[2])           
    c = abs(quan[2]-quan[3])
    d = abs(quan[3]-quan[4])
    minimum = min(a,b,c,d)             
    if minimum == a:                   
        rang = quan[0], quan[1]
    elif minimum == b:
        rang = quan[1], quan[2]
    elif minimum == c:
        rang = quan[2], quan[3]
    else:
        rang = quan[3], quan[4]
    subset_3 = subset_2[(subset_2.price>= rang[0]) & (subset_2.price<= rang[1])]
    ideal_price = subset_3.price.mean()
    if mar >= rang[0] and mar <= rang[1]:
      r=1
    else:
      r=0  
    output_list.append([crawl_date,sku, p, mar, m, mode, quan, rang, l_org, l, r, ideal_price])
  
  output = pd.DataFrame(output_list)
  output.columns = ['crawl_date','Product SKU','Product Name', 'Market Price', 'Median', 'Mode', 'Quantiles', 'Price Range','Number of Observations', 'Number of Observations After Multiplication', 'Result', 'Ideal Price']
  last_df = pd.merge(last_df,output[['Product SKU', 'Price Range', 'Ideal Price']], left_on = 'product_code', right_on = 'Product SKU', how = 'left')
  # Fix column types and round 
  last_df['Ideal Price'] = last_df['Ideal Price'].astype('float').round(2)
  #last_df['Price Range'] = last_df['Price Range'].astype(float).round(2)
  last_df['Category Mean Rank'] = last_df['Category Mean Rank'].astype('float').round(2)
  last_df['Overall_median_price'] = last_df['Overall_median_price'].astype('float').round(2)
  last_df['Overall_mean_price'] = last_df['Overall_mean_price'].astype('float').round(2)
  last_df['wavg price'] = last_df['wavg price'].astype('float').round(2)

  last_df = last_df.drop(['Product SKU'], axis=1)

  #Creating separate columns for Brand, Amazon, Mediamarkt prices

  results["Compare"] =  [x[0].lower() in x[1].lower() for x in zip(results['brand_name'], results['link_only'])]
  brands_df = results[results.Compare != False]
  brands_df_prices = brands_df[['product_code','price']].copy()
  brands_df_prices.rename(columns = {'price':'brand_price'}, inplace = True) 
  last_df = last_df.merge(brands_df_prices, how = 'left' ,on = 'product_code')
  last_df.rename(columns = {'name_x':'product_name', 'category.name_x': 'category_name', 'cost':'inhouse_RRP'}, inplace = True)

  # creating a column for Amazon Prices

  results["Amazon_prices"] = results['link_only'].str.contains('amazon')
  Amazon_prices = results[results.Amazon_prices != False]
  Amazon_prices_df = Amazon_prices[['product_code','price']].copy()
  Amazon_prices_df.rename(columns = {'price':'Amazon_prices'}, inplace = True) 
  last_df = last_df.merge(Amazon_prices_df, how = 'left' ,on = 'product_code')


  # creating a column for Mediamarkt Prices

  results["Mediamarkt_prices"] = results['link_only'].str.contains('mediamarkt')
  Mediamarkt_prices = results[results.Mediamarkt_prices != False]
  Mediamarkt_prices_df = Mediamarkt_prices[['product_code','price']].copy()
  Mediamarkt_prices_df.rename(columns = {'price':'Mediamarkt_prices'}, inplace = True) 
  last_df = last_df.merge(Mediamarkt_prices_df, how = 'left' , on = 'product_code')

  last_df["crawl_date"] = date_today
  #print(last_df.columns)
  
  # Working on sqlite database  
  print_exclaim("Updating local database with new data")
  conn = sqlite3.connect(database_filename)
  output = last_df.applymap(str)
  output.to_sql(name='data_output', con=conn, if_exists = 'append')
  conn.commit()

  # Run a check
  new_df2 = pd.read_sql_query('SELECT * FROM data_output',conn)
  conn.close()
  print_check("Local database updated")

  # Check for duplicate rows
  if new_df2[new_df2.duplicated()].empty != True:
    print_exclaim("Duplicate rows identified in dataframe.")
    print_exclaim("Please check")
  
  # Update google drive with new database
  print_exclaim("Updating database in gdrive")
  upload_pricsync_US(database_filename)
  print_check("Database updated in gdrive")

  # Updating gsheet
  print_exclaim("Updating spreadsheet with latest data")
  response = upload_df_to_gsheet_US(output)
  #print_check(response)
  print_check("Spreadsheet update complete")





