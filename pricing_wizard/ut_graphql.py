# Check authentication
import requests
import json

url    = 'https://apiqa.getgrover.com/api/v1/oauth/token'
header = {'Content-Type': 'application/json'}
# Provide username and password in plain text here for now
body   = {"email": "ian.connelly@grover.com", "password": "", "grant_type": "password" }
y = json.dumps(body)

x = requests.post(url, headers=header, data=y)

print (x)
print (x.text)
token = json.loads(x.text)["access_token"]
print (token)

# Check graphql
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

# Select your transport with a defined url endpoint
auth_header = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
transport = AIOHTTPTransport(url='https://graphql-staging.grover.com/graphql', headers=auth_header)

# Create a GraphQL client using the defined transport
client = Client(transport=transport, fetch_schema_from_transport=True)

query = gql('''
	mutation {
	  createS3PresignedUrl(input: {
	    bucket: "catalog_jobs_uploads_staging",
	    fileName: "20220601_Ian.xlsx"
	  }) {
	    ... on PresignedUrl {
	      fileUri
	    }
	  }
	}
	
''')

print (query)
result = client.execute(query)
fileUri = result["createS3PresignedUrl"]["fileUri"]

query = gql('''
	mutation {
  	  taskCreateRentalPlanUpload(input: {
        fileUri: "'''+fileUri+'''" # your file- needs to match to the variable of createS3PresignedUrl mutation
        fileName: "PriWizTest-2022-06-01.xls", # will be visible in admin-panel list
        scheduledFor: "2022-06-02T00:00:00.000Z" # date iso string
       }) {
    ... on RentalPlanUploadTask {
      id
    }
    ... on TaskError {
      message
    }
  }
}
''')

result = client.execute(query)
print (result)

print (result)