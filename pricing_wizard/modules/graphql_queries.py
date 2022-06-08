# This file can hold any GraphQL queries needed for pricing in Admin Panel
# Note for f-strings, we use double braces for a single brace in the string

def upload_to_S3_staging(filename):
	query_string = f"""
		mutation {{
			createS3PresignedUrl(input: {{
				bucket: "catalog-jobs-uploads-staging",
				fileName: "{filename}"
			}}) {{
				... on PresignedUrl {{
					fileUri
				}}
			}}

		}}
	"""
	return query_string

def upload_to_S3_production(filename):
	query_string = f"""
		mutation {{
			createS3PresignedUrl(input: {{
				bucket: "catalog-jobs-uploads-production",
				fileName: "{filename}"
			}}) {{
				... on PresignedUrl {{
					fileUri
				}}
			}}

		}}
	"""
	return query_string

def upload_to_admin_panel(fileUri, adminPanelName, scheduledTime):
	# Important to validate the scheduledTime string format explictly
	import re
	date_regex_str     = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z$"
	date_regex_pattern = re.compile(date_regex_str)
	check_datetime     = date_regex_pattern.match(scheduledTime)

	if not check_datetime:
		raise ValueError(f"Incorrect scheduled date-time format for AdminPanel upload {scheduledTime}")

	query_string = f"""
		mutation {{
			taskCreateRentalPlanUpload(input : {{
				fileUri: "{fileUri}",
				fileName: "{adminPanelName}",
				scheduledFor: "{scheduledTime}"
			}}) {{
				... on RentalPlanUploadTask {{
					id
				}}
				... on TaskError {{
					message
				}}
			}}
		}}
	"""
	return query_string
