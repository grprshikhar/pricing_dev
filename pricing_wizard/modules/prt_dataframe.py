import pandas as pd
import itertools
import modules.gsheet as gsheet
from modules.options_handler import options_handler
from modules.print_utils import tabulate_dataframe, print_check, print_exclaim
import modules.gsheet as gsheet
import numpy as np

# this class collects the data from different sheets and combines them into 1 dataframe 
def data_collector():
  #downloading the required data to build the dataframe needed
  # incoming stock
  incoming_stock = gsheet.get_dataframe("1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew","Stock!A:G","Incoming stock")
  incoming_stock = incoming_stock[['product_sku', 'incoming (proc data)']]
  print(incoming_stock)

  #Stock in hand with incoming
  stock_with_incoming = gsheet.get_dataframe("1MvFH_AIoHwXzYKhZVrrCpyU-Xk0onhkXyhke1wufjfI","SKU Availability!A:E","SOH with incoming")
  stock_with_incoming = stock_with_incoming[['sku', 'available+incoming']].copy()
  stock_with_incoming.rename(columns = {'sku':'product_sku'}, inplace = True)
  print(stock_with_incoming)

  #Stock in hand without incoming
  stock_without_incoming = gsheet.get_dataframe("1MvFH_AIoHwXzYKhZVrrCpyU-Xk0onhkXyhke1wufjfI","SKU Availability!A:E","SOH without incoming")
  stock_without_incoming = stock_without_incoming[['sku','sum availablecount']].copy()
  stock_without_incoming.rename(columns = {'sku':'product_sku'}, inplace = True)
  print(stock_without_incoming)

  # Average Age per SKU
  avg_age = gsheet.get_dataframe("1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew","Age!A:E","avg_age(days)")
  avg_age = avg_age[['product_sku','avg_age(days)']]
  print(avg_age)

  months_old = gsheet.get_dataframe("1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew","Age!A:E","months_old")
  months_old = months_old[['product_sku','months_old']]
  print(months_old)

  #Aquired subs last 30 days 
  acquired_subs = gsheet.get_dataframe("1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew","Acq. Subs!A:C","Acq Subs (Last 30 days)")
  acquired_subs = acquired_subs[['product_sku','acq subs (last 30 days)']]
  print(acquired_subs)

  # normalised acquried subs
  normalised_acquired_subs = gsheet.get_dataframe("1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew","MOS!A:I","Normalised Acquired Subs")
  normalised_acquired_subs = normalised_acquired_subs[['product_sku','normalised']]
  print(normalised_acquired_subs)

  # MOS with incoming 
  mos_incoming = gsheet.get_dataframe("1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew","MOS!A:I","MOS(Proc Data)")
  mos_incoming = mos_incoming[['product_sku','mos(proc data)']]
  print(mos_incoming)

  # Days out of stock
  days_oos = gsheet.get_dataframe("1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew","Days OOS!A:B","count")
  days_oos = days_oos[['product_sku','count']]
  print(days_oos)

  # Number of submitted orders last 30 days 
  submitted_orders = gsheet.get_dataframe("1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew","Submitted orders last 30 days!A:B","number_of_submitted_orders")
  submitted_orders = submitted_orders[['product_sku','number_of_submitted_orders']]
  print(submitted_orders)

  # PP & RRP Percentages
  pp_perc = gsheet.get_dataframe("1XpMzxJrcjs6o0sOzIQB9JE4rhXFq9dZJkufkzeO5hfs","RRP&PP!A:AI","pp_perc")
  pp_perc = pp_perc[['product_sku','m1_pp_perc','m3_pp_perc','m6_pp_perc','m12_pp_perc','m18_pp_perc','m24_pp_perc']]
  pp_perc.drop_duplicates()
  print(pp_perc)

  rrp_perc = gsheet.get_dataframe("1XpMzxJrcjs6o0sOzIQB9JE4rhXFq9dZJkufkzeO5hfs","RRP&PP!A:AI","rrp_perc")
  rrp_perc = rrp_perc[['product_sku','m1_rrp_perc','m3_rrp_perc','m6_rrp_perc','m12_rrp_perc','m18_rrp_perc','m24_rrp_perc','any_discounted']]
  rrp_perc.drop_duplicates()
  print(rrp_perc)

  # Average purchase Age
  avg_purchase_age = gsheet.get_dataframe("1HbL--6GmFC-Kupwpaw3XcSFC7xQO1MRRgixG7OqF8Ew","Age!A:E","avg_purchase_age(months)")
  avg_purchase_age = avg_purchase_age[['product_sku','avg_purchase_age(months)']]
  print(avg_purchase_age)

  # Daily ASV with stock per view this session
  daily_asv = gsheet.get_dataframe("1YnaSO7P3ck2-xej3NFQL1GAlG9EuR6pS29pBRI2-44w","Last 3M Live Submitted DE!A:AD","daily_asv_w_stock_per_view_this_session")
  daily_asv = daily_asv[['product_sku','daily_asv_w_stock_per_view_this_session','daily_asv_w_stock_per_view_prev_session']]
  daily_asv.drop_duplicates()
  print(daily_asv)

  # Daily ASV with stock per view previous session
  #daily_asv_w_stock_per_view_prev_session = gsheet.get_dataframe("1YnaSO7P3ck2-xej3NFQL1GAlG9EuR6pS29pBRI2-44w","Last 3M Live Submitted DE!A:AD","daily_asv_w_stock_per_view_prev_session")
  #daily_asv_w_stock_per_view_prev_session = daily_asv_w_stock_per_view_prev_session[['product_sku','daily_asv_w_stock_per_view_prev_session']]
  #print(daily_asv_w_stock_per_view_prev_session)

  # Organic traffic last 4 weeks 
  organic_traffic_last_4weeks = gsheet.get_dataframe("1zB8QTkvXZXQc0ttdAIePuuuUhokhnHxHkrerO4CEeeg","Marketing&Performance!A:AB","organic_traffic_last_4weeks")
  organic_traffic_last_4weeks = organic_traffic_last_4weeks[['product_sku','organic_traffic_last_4weeks']]
  print(organic_traffic_last_4weeks)

  # Discounted
  #discounted = gsheet.get_dataframe("1XpMzxJrcjs6o0sOzIQB9JE4rhXFq9dZJkufkzeO5hfs","RRP&PP!A:AI","any_discounted")
  #discounted = discounted[['product_sku','any_discounted']]
  #print(discounted)


  # Merging the dataframes into one
  main_df = pd.merge(stock_with_incoming, stock_without_incoming, on = 'product_sku', how = 'left')
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, incoming_stock, on = 'product_sku', how = 'left')
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, avg_age, on = 'product_sku', how = 'left')
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, months_old, on = 'product_sku', how = 'left')
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, acquired_subs, on = 'product_sku', how = 'left') 
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, mos_incoming, on = 'product_sku', how = 'left') 
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, days_oos, on = 'product_sku', how = 'left') 
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, submitted_orders, on = 'product_sku', how = 'left') 
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, avg_purchase_age, on = 'product_sku', how = 'left') 
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, daily_asv, on = 'product_sku', how = 'left') 
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, organic_traffic_last_4weeks, on = 'product_sku', how = 'left') 
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, normalised_acquired_subs, on = 'product_sku', how = 'left') 
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df = pd.merge(main_df, pp_perc, on = 'product_sku', how = 'left')
  print(main_df.shape)
  main_df.drop_duplicates()
  main_df.to_csv("before_crash.csv")
  main_df = pd.merge(main_df, rrp_perc, on = 'product_sku', how = 'left')
  main_df.drop_duplicates()
  print(main_df.shape)

  print("ALL merges done")

  # Data Cleaning and formatting 
  main_df.rename(columns = {'count':'days_oos'}, inplace = True)
  main_df.rename(columns = {'sum availablecount':'stock_without_incoming'}, inplace = True)
  main_df.rename(columns = {'available+incoming':'stock_with_incoming'}, inplace = True)

  print("ALL DATA CLEANED")
  main_df['stock_without_incoming'] = pd.to_numeric(main_df['stock_without_incoming'], errors='coerce')
  main_df['normalised'] = pd.to_numeric(main_df['stock_without_incoming'], errors='coerce')

  main_df['mos_without_incoming'] = main_df['stock_without_incoming'] / main_df['normalised']

  main_df['number_of_submitted_orders'] = pd.to_numeric(main_df['number_of_submitted_orders'], errors='coerce')
  main_df['organic_traffic_last_4weeks'] = pd.to_numeric(main_df['organic_traffic_last_4weeks'], errors='coerce')

  main_df['CR'] = main_df['number_of_submitted_orders'] / main_df['organic_traffic_last_4weeks']
  print("Data Cleaned and formatted and ready to use")

  main_df.to_csv("main_df_Final.csv")





