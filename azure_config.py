import json
import azure.batch as batch
from azure.storage.blob import BlobServiceClient
import azure.batch.batch_auth as batch_auth
import azure.batch.models as batch_models
from node import Node
import time
from datetime import datetime, timedelta, UTC
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
import requests
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')

with open(config_path) as f:
    config = json.load(f)


class Token:
    def __init__(self, credential, scope):
        self.credential = credential
        self.scope = scope
        self._cached_token = None
        self._expires_on = None

    def _refresh_token(self):
        token = self.credential.get_token(self.scope)
        self._cached_token = token.token
        self._expires_on = datetime.fromtimestamp(token.expires_on, tz=UTC)

    def get_token(self):
        now = datetime.now(UTC)
        if (
            self._cached_token is None or
            self._expires_on is None or
            (now + timedelta(minutes=5)) > self._expires_on
        ):
            self._refresh_token()
        return self._cached_token

    def signed_session(self):
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.get_token()}"
        })
        return session

credential = DefaultAzureCredential()
managed_credential = ManagedIdentityCredential(client_id="51f8e85c-c8d8-48fa-a729-386bb50e8838")
aad_scope = "https://batch.core.windows.net/.default"
token = Token(credential, aad_scope)
managed_token = Token (managed_credential, aad_scope)

blob_service_client = BlobServiceClient(account_url=config["azure-blob-account-url"], credential=credential)
vm_blob_service_client = BlobServiceClient(account_url=config["azure-blob-account-url"], credential=managed_credential)
def url_as_blob_name(url):
    return f"{url}.html" 

def init_batch_client():
    """Initialize Azure Batch client."""
   # credentials = batch_auth.SharedKeyCredentials(config["azure-batch-account-name"], config["azure-batch-account-key"])
    return batch.BatchServiceClient(credentials=token, batch_url=config["azure-batch-account-url"])


def blob_to_data(blob):
    blob_client = blob_service_client.get_blob_client(container=config["container-name"], blob=blob)
    downloaded_blob = blob_client.download_blob() # Download blob from Azure container
    return json.loads(downloaded_blob.readall())

def node_from_json_data(node_data, seen, lock, rules):
    # Initialize Node object
    node = Node(node_data['url'], node_data['parent'])
    node.set_relevance(node_data['relevance'])
    links = node_data["links"]
    for link in links:
        with lock:
            if link not in seen:
                if rules.url_is_allowed(link):
                    seen.add(link)
                    child = node.Node(link, node)
                    node.add_child(child)

    return node

def get_job_id(url, batch_client):
    """Names the job according to the supplied URL and checks that it does not exist already."""
    job_id = f"gather-job-{url.replace('https://', '').replace('/', '_').replace('.', '-')}"

    try:
        existing_job = batch_client.job.get(job_id)  # Check if job exists
        print(f"Deleting existing job: {job_id}")
        batch_client.job.delete(job_id)  # Delete the existing job
        while True:
            try:
                batch_client.job.get(job_id)  # Check if job still exists
                print(f"Waiting for job {job_id} to be deleted...")
                time.sleep(5)  # Wait before checking again
            except batch_models.BatchErrorException:
                print(f"Job {job_id} deleted successfully.")
                break
    except batch_models.BatchErrorException as e:
        if "The specified job does not exist" in str(e):
            pass  
        else:
            raise  

    return job_id