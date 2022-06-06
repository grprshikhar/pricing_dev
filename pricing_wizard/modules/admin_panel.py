import requests
import json
import gql
from getpass import getpass
from gql.transport.aiohttp import AIOHTTPTransport
from modules.graphql_queries import upload_to_S3, upload_to_admin_panel
from modules.print_utils import print_exclaim, print_check

# This class handles authorisation for uploads to Admin Panel
class admin_panel(object):
	def __init__(self, run_opts):
		self.graphql_client = None
		self.auth_token     = None
		self.run_opts       = run_opts

	def authorise(self):
		if self.auth_token:
			print_check("Using existing authorisation token for Admin Panel")
			return
		# Collect Admin Panel credentials
		print_exclaim("Preparing authorisation with Admin Panel")
		user = self.run_opts.get_adminpanel_username()
		pwd  = getpass("Enter AdminPanel password :: ")
		# Submit POST request for authorisation
		url    = 'https://apiqa.getgrover.com/api/v1/oauth/token'
		header = {'Content-Type': 'application/json'}
		body   = {"email": user, "password": pwd, "grant_type": "password" }
		# Submit the authorisation request
		auth_request = requests.post(url, headers=header, data=json.dumps(body))
		# Store authorisation token
		try:
			self.auth_token = json.loads(auth_request.text)["access_token"]
		except:
			raise ValueError(f"Admin Panel authorisation failed [{user}]")
		print_check(f"Admin Panel authorisation complete [{user}]")

	def configure(self):
		# If not authorised, perform authorisation
		if not self.auth_token:
			self.authorise()
		# Check if client already exists
		if self.graphql_client:
			return
		# Build POST request for client
		url         = "https://graphql-staging.grover.com/graphql"
		auth_header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {self.auth_token}'}
		transport   = AIOHTTPTransport(url, headers=auth_header)
		# Create client
		self.graphql_client = gql.Client(transport=transport, fetch_schema_from_transport=True)

	def upload_pricing(self, pricingFileName, adminPanelName, scheduledTime):
		# Step 1 - Ensure client is configured
		self.configure()

		# Step 2 - Upload to Amazon S3 location
		query   = gql.gql( upload_to_S3(pricingFileName) )
		result  = self.graphql_client.execute( query )
		fileUri = result["createS3PresignedUrl"]["fileUri"]
		print_check(f"File {pricingFileName} uploaded to Amazon S3")

		# Step 3 - Provide S3 location to Admin Panel 
		query  = gql.gql( upload_to_admin_panel(fileUri, adminPanelName, scheduledTime) )
		result = self.graphql_client.execute(query)
		apID   = result["taskCreateRentalPlanUpload"]["id"]
		print_check(f"Admin Panel upload complete [ID : {apID}]")





