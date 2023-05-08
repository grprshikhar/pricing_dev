#Imports
import os
import pandas as pd
import modules.gsheet as gsheet
from modules.print_utils import print_exclaim

def msh_process_dataframes():

  # Check if values exist in the first two columns and the rest of the columns are empty
  def filter_rows(df):
      mask = (df.iloc[:, 0].notna() & df.iloc[:, 1].notna() &
              df.iloc[:, 2:].apply(lambda x: x == '').all(axis=1))
      return df[mask]


  # Function to remove rows with the same SKU in another DataFrame
  def remove_rows_with_same_sku(df1, df2):
      skus_to_remove = df2['sku']
      mask = ~df1['sku'].isin(skus_to_remove)
      return df1[mask]


  # Function to export chunks of the DataFrame as separate xlsx files
  def export_chunks(df, folder_name, chunk_size=24):
      num_chunks = (len(df) - 1) // chunk_size + 1
      
      # Create a folder to store the xlsx files
      if not os.path.exists(folder_name):
          os.makedirs(folder_name)
      
      for i in range(num_chunks):
          chunk = df.iloc[i * chunk_size: (i + 1) * chunk_size]
          filename = os.path.join(folder_name, f'chunk_{i+1}.xlsx')
          chunk.to_excel(filename, index=False)
          print(f'Exported {filename}')



  print_exclaim("Downloading Data From Google Sheets")

  # MM offline data
  export_mm_offline = gsheet.get_dataframe("1Mnd7AGuL5dxzi0oIoUYC7DkljqQR0jyBTpH7tU3llmQ", "Export_MM_Offline!A:AD", "Export_MM_Offline")
  # Saturn offline data
  export_saturn_offline = gsheet.get_dataframe("1Mnd7AGuL5dxzi0oIoUYC7DkljqQR0jyBTpH7tU3llmQ", "Export_Saturn_Offline!A:AD", "Export_Saturn_Offline")

  print_exclaim("Formatting and splitting MSH upload files")

  # Filtering and downloading Mediamarkt data
  empty_mm = filter_rows(export_mm_offline)
  filtered_mm_df = remove_rows_with_same_sku(export_mm_offline, empty_mm)
  export_chunks(empty_mm, 'exported_empty_mm_chunks')
  export_chunks(filtered_mm_df, 'exported_mm_chunks_filtered')

  # Filtering and downloading Saturn data
  empty_saturn = filter_rows(export_saturn_offline)
  filtered_saturn_df = remove_rows_with_same_sku(export_saturn_offline, empty_saturn)
  export_chunks(empty_saturn, 'exported_empty_saturn_chunks')
  export_chunks(filtered_saturn_df, 'exported_saturn_chunks_filtered')







