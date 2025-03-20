import os
import pandas as pd
import modules.gsheet as gsheet
from pandas import ExcelWriter
# System imports
import datetime
import pytz
import re
# Module imports
import modules.gdrive as gdrive
import modules.catman_utils as catman_utils
#import modules.redshift_manager as redshift_manager
from modules.admin_panel import admin_panel
from modules.print_utils import print_check, print_exclaim, print_green, tabulate_dataframe





class msh_process_dataframes(object):
    def __init__(self, run_opts):
        print_exclaim("Downloading Data From Google Sheets")
        # OLD 1Mnd7AGuL5dxzi0oIoUYC7DkljqQR0jyBTpH7tU3llmQ
        # MM offline data 
        self.export_mm_offline = gsheet.get_dataframe("1HV742fLqrCi28r7mis6h4Nut2vkeltYiU5N_Dw5Qlqo", "Export MM Offline!A:AD", "Export MM Offline")
        # Saturn offline data
        self.export_saturn_offline = gsheet.get_dataframe("1HV742fLqrCi28r7mis6h4Nut2vkeltYiU5N_Dw5Qlqo", "Export SAT Offline!A:AD", "Export SAT Offline")
        self.run_opts = run_opts
        self.admin = admin_panel(self.run_opts, True)        
        template_name = gdrive.download_partner_template()
        template_df   = pd.read_excel(template_name, sheet_name=None)
        self.rental_plans_export_mm_offline = template_df["rental_plans"]
        self.rental_plans_export_saturn_offline = template_df["rental_plans"]
        # Clean any NaN again
        self.rental_plans_export_mm_offline = self.rental_plans_export_mm_offline.fillna('')
        self.rental_plans_export_saturn_offline = self.rental_plans_export_saturn_offline.fillna('')
        # Configure output file name
        # Today date matching existing format could also use .date().isoformat()
        today_date    = datetime.datetime.today().strftime("%Y%m%d")
        # The user who is doing work
        #username      = self.run_opts.current_user
        # Construct the file name
        #out_filename  = f"{today_date}_{username}"
        self.rental_plans_export_mm_offline[['SKU','Partner Name','Newness', 'Newness expiration date', 'Price Change Reason', 'Price Change Tag','1','3','6','12','18','24']] = self.export_mm_offline[['sku','partner name','newness', 'newness expiration date', 'price change reason', 'price change tag','1','3','6','12','18','24']].copy()
        self.rental_plans_export_saturn_offline[['SKU','Partner Name','Newness', 'Newness expiration date', 'Price Change Reason', 'Price Change Tag','1','3','6','12','18','24']] = self.export_saturn_offline[['sku','partner name','newness', 'newness expiration date', 'price change reason', 'price change tag','1','3','6','12','18','24']].copy()
        
    def filter_rows(self, df):
        mask = (df.iloc[:, 0].notna() & df.iloc[:, 1].notna() &
                df.iloc[:, 2:].apply(lambda x: x == '').all(axis=1))
        return df[mask]

    def remove_rows_with_same_sku(self, df1, df2):
        skus_to_remove = df2['SKU']
        mask = ~df1['SKU'].isin(skus_to_remove)
        return df1[mask]

    def remove_files_in_path(self, folder_path):
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            for file in files:
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f'Deleted {file_path}')
        else:
            print(f'Folder {folder_path} does not exist.')
    

    def export_chunks(self, df, folder_name, chunk_size=24):
        num_chunks = (len(df) - 1) // chunk_size + 1
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        else:
            self.remove_files_in_path(folder_name)

        for i in range(num_chunks):
            self.now = self.now + datetime.timedelta(seconds=60)
            t = pytz.timezone('Europe/Berlin').localize(self.now,is_dst=None)
            scheduledTime = (t).isoformat(timespec='milliseconds')[:-6]+"Z"
            print(i, num_chunks, scheduledTime)
            chunk = df.iloc[i * chunk_size: (i + 1) * chunk_size]
            filename = os.path.join(folder_name, f'chunk_{i+1}.xls')
            #chunk.to_excel(filename, index=False, engine='xlsxwriter')
            with pd.ExcelWriter(filename) as writer:
                chunk.to_excel(writer, sheet_name= "rental_plans",index=False)
            # Schedule with incremental time
            self.admin.upload_pricing(filename, filename, scheduledTime)
            
            print(f'Exported {filename}')

    def process_data(self):
        print_exclaim("Formatting and splitting MSH upload files")

        # Filtering and downloading Mediamarkt data
        empty_mm = self.filter_rows(self.rental_plans_export_mm_offline)
        filtered_mm_df = self.remove_rows_with_same_sku(self.rental_plans_export_mm_offline, empty_mm)
        self.now = datetime.datetime.now() + datetime.timedelta(seconds=30)
        self.export_chunks(empty_mm, 'exported_empty_mm_chunks')
        self.now = datetime.datetime.now() + datetime.timedelta(seconds=30)
        self.export_chunks(filtered_mm_df, 'exported_mm_chunks_filtered')

        # Filtering and downloading Saturn data
        empty_saturn = self.filter_rows(self.rental_plans_export_saturn_offline)
        filtered_saturn_df = self.remove_rows_with_same_sku(self.rental_plans_export_saturn_offline, empty_saturn)
        self.now = datetime.datetime.now() + datetime.timedelta(seconds=30)
        self.export_chunks(empty_saturn, 'exported_empty_saturn_chunks')
        self.now = datetime.datetime.now() + datetime.timedelta(seconds=30)
        self.export_chunks(filtered_saturn_df, 'exported_saturn_chunks_filtered')





