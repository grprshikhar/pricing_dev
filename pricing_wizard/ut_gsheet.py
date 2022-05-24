from modules.gsheet import pull_sheet_data, SCOPES
import pandas as pd

# Spreadsheet
sheet_id = '1r_LxoZd33ewZhPt9hp8lda4RPU05F94PWrgML1-PocU'
# Data range
data_range = 'Export!A:M'
# Returns the data requested (nb SCOPES is from module)
data = pull_sheet_data(SCOPES,sheet_id,data_range)
# Convert to pandas dataframe
df = pd.DataFrame(data[1:], columns=data[0])
print (df.head(20))