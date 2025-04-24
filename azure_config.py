import json
import warnings
import azure.batch as batch
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError, AzureError
import azure.batch.batch_auth as batch_auth
import azure.batch.models as batch_models
import time
from datetime import datetime, timedelta, UTC
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
import requests
import os

"""Configuration"""
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')

with open(config_path) as f:
    config = json.load(f)

warnings.filterwarnings("ignore", module="azure")


"""Token Class that refreshes"""
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

"""Azure credentials and client variables"""
credential = DefaultAzureCredential()
aad_scope = "https://batch.core.windows.net/.default"
token = Token(credential, aad_scope)

managed_credential = ManagedIdentityCredential(client_id="51f8e85c-c8d8-48fa-a729-386bb50e8838")

blob_service_client = BlobServiceClient(account_url=config["azure-blob-account-url"], credential=credential)
vm_blob_service_client = BlobServiceClient(account_url=config["azure-blob-account-url"], credential=managed_credential)

"""Utility functions for Azure connections"""

def init_batch_client():
    """Initialize Azure Batch client."""
   # credentials = batch_auth.SharedKeyCredentials(config["azure-batch-account-name"], config["azure-batch-account-key"])
    return batch.BatchServiceClient(credentials=token, batch_url=config["azure-batch-account-url"])

def blob_to_data(blob):
    """Downloads a blob and loads JSON data."""
    blob_client = blob_service_client.get_blob_client(container=config["container-name"], blob=blob)
    downloaded_blob = None
    for i in range(100):
        try:
            downloaded_blob = blob_client.download_blob() # Download blob from Azure container
            break
        except ResourceNotFoundError:
            time.sleep(1)

    if downloaded_blob is not None:
        return json.loads(downloaded_blob.readall())
    else:
        print(f"timed out waiting for {blob}")
        return None

def get_job_id(url, batch_client):
    """Names the job according to the supplied URL and checks that it does not exist already."""
    job_id = f"gather-job-{url.replace('https://', '').replace('http://', '').replace('/', '_').replace('.', '-')}"

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