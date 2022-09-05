import requests
import json
import gql
from modules.get_password import getpass
from gql.transport.aiohttp import AIOHTTPTransport
from modules.graphql_queries import upload_to_S3_staging, upload_to_S3_production, upload_to_admin_panel
from modules.print_utils import print_exclaim, print_check

# This class handles authorisation for uploads to Admin Panel
class admin_panel(object):
	def __init__(self, run_opts, to_production=False):
		self.graphql_client = None
		self.auth_token     = None
		self.run_opts       = run_opts
		self.to_production  = to_production
		self.retries        = 5
		self.define_urls()

	def define_urls(self):
		# Different locations for production and staging sites
		if self.to_production:
			self.authorisation_url = "https://api.getgrover.com/api/v1/oauth/token"
			self.graphql_url       = "https://graphql.grover.com/graphql"
		else:
			self.authorisation_url = "https://apiqa.getgrover.com/api/v1/oauth/token"
			self.graphql_url       = "https://graphql-staging.grover.com/graphql"
		print_check(f"Configured Admin Panel tool for {'Production' if self.to_production else 'Staging'} site")
		# print_check(f"Authorisation URL : {self.authorisation_url}")
		# print_check(f"GraphQL URL       : {self.graphql_url}")

	def authorise(self):
		if self.auth_token:
			print_check("Using existing authorisation token for Admin Panel")
			return
		# Collect Admin Panel credentials
		print_exclaim("Preparing authorisation with Admin Panel")
		user = self.run_opts.get_adminpanel_username()
		pwd  = getpass("Enter AdminPanel password :: ")

		# Submit POST request for authorisation
		header = {'Content-Type': 'application/json'}
		body   = {"email": user, "password": pwd, "grant_type": "password" }
		# Submit the authorisation request
		auth_request = requests.post(self.authorisation_url, headers=header, data=json.dumps(body))
		# Store authorisation token
		try:
			self.auth_token = json.loads(auth_request.text)["access_token"]
		except:
			print(f"Admin Panel authorisation failed [{user}]")
			# Reset token
			self.auth_token = None
			# Rerun
			self.authorise()
			
		print_check(f"Admin Panel authorisation complete [{user}]")

	def configure(self):
		# If not authorised, perform authorisation
		if not self.auth_token:
			self.authorise()
		# Check if client already exists
		if self.graphql_client:
			return
		# Create client
		auth_header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.auth_token}'}
		transport   = AIOHTTPTransport(self.graphql_url, headers=auth_header)
		# Create client
		self.graphql_client = gql.Client(transport=transport, fetch_schema_from_transport=False)

	def put_to_S3(self, pricingFileName, pricingFileUri):
		# This manages the upload to S3
		data = open(pricingFileName,"rb").read()
		r = requests.put(pricingFileUri, data=data)
		return r.status_code

	def upload_pricing(self, pricingFileName, adminPanelName, scheduledTime):
		# Step 1 - Ensure client is configured
		self.configure()

		# Step 2 - Generate the upload url
		# Staging S3 location
		if not self.to_production:
			query = gql.gql( upload_to_S3_staging(pricingFileName) )
		# Production S3 location
		else:
			query = gql.gql( upload_to_S3_production(pricingFileName) )
		result  = self.graphql_client.execute( query )
		fileUri = result["createS3PresignedUrl"]["fileUri"]

		# Step 2.5 - Perform the PUT request to upload the file
		status  = self.put_to_S3(pricingFileName, fileUri)
		# Check that the status code is OK
		if status != 200:
			raise ValueError(f"Error uploading to S3 [code : {retcode}]")
		print_check(f"File {pricingFileName} uploaded to Amazon S3")

		# Step 3 - Provide information (filename, name, scheduled time) to Admin Panel
		query  = gql.gql( upload_to_admin_panel(pricingFileName, adminPanelName, scheduledTime) )
		result = self.graphql_client.execute(query)
		try:
			apID   = result["taskCreateRentalPlanUpload"]["id"]
			print_check(f"Admin Panel upload complete [ID : {apID}]")
		except:
			raise ValueError(f"Error in final transfer of information to Admin Panel [{result}]")





