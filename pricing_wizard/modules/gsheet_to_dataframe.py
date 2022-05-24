import modules.gsheet as gsheet
import pandas

def get_dataframe(sheet_id, data_range):
	# Get data from gsheet
	data = gsheet.pull_sheet_data(gsheet.SCOPES, sheet_id, data_range)
	# Convert data (arrays) into dataframe
	df = pandas.DataFrame(data)
	# Extract first row as header
	header = df.iloc[0]
	# Remove first row from dataframe
	df = df[1:]
	# Set column names
	df.columns = header
	# Reset indexing after removing row
	df = df.reset_index(drop=True).copy()
	# Clean any NaN
	df.fillna("",inplace=True)
	# Convert header names to consistent capitalisation
	df.columns = [x.lower() for x in df.columns]
	# Return the dataframe
	return df