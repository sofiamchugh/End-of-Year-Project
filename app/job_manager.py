
import azure.batch.models as batch_models
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from user_agent import UserAgent
from node import Node
from azure.core.exceptions import ResourceNotFoundError, AzureError
import sys, time, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from util.util import make_safe_task_id, url_as_blob_name
from azure_modules.azure_config import init_batch_client, config, blob_service_client, delete_job_if_exists


COMMAND_LINE_PATH = (
    "/bin/bash -c '"
    "export PLAYWRIGHT_BROWSERS_PATH=/mnt/batch/tasks/shared/playwright-browsers && "
    "/mnt/batch/tasks/shared/venv/bin/python3 /mnt/batch/tasks/shared/repo"
)

class JobManager:
    def __init__(self, app, job_id):
        self.batch_client = init_batch_client()
        self.app = app
        self.job_id = job_id
        self.futures = set()
        self.rules = UserAgent()
        self.seen = set()
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers = 3)
        self.init_job(job_id)

    def init_job(self, job_id):
        """Configure job in Azure Batch."""
        delete_job_if_exists(job_id, self.batch_client)
        try: 
            job = batch_models.JobAddParameter(
                    id=job_id, pool_info=batch_models.PoolInformation(pool_id=config["pool-id"])
                )
            self.batch_client.job.add(job)
        except Exception as e:
            print("failed to create job")

    def create_task(self, node):
        """Creates the task that executes worker.py in an Azure VM node."""
        crawl_delay = self.rules.crawl_delay
        task_id = make_safe_task_id(node.url)
        args = f"{node.url} {node.parent} {crawl_delay}"
        command_line = f"{COMMAND_LINE_PATH}/ azure_modules.worker.py {args}"
        return batch_models.TaskAddParameter(id=task_id, command_line=command_line)

    def submit_task(self, task, url):
        """Submits task to batch client and starts get_blob to download results from Azure."""
        self.batch_client.task.add(self.job_id, task)
        self.futures.add(self.executor.submit(self.get_blob, url))

    def get_blob(self, url):
        """Gets the blob from Azure, processes into node, and starts processing children."""
        blob_name = url_as_blob_name(url)
        crawl_delay = self.rules.crawl_delay
        node, new_delay = self.process_azure_info(blob_name)
        self.update_crawl_delay(new_delay, crawl_delay)
        self.process_children(node)
    
    def blob_to_data(self, blob):
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
        
    def process_azure_info(self, blob_name):
        """Download blobs from Azure and converts them to nodes to be displayed in-app. """

        data = self.blob_to_data(blob_name) #downloads blob from azure
        node = Node(None, None)
        
        node.node_from_json(data, self.app)
        self.app.data_queue.put(node) # Put node in queue to be added to graph

        new_delay = data["crawl_delay"] 
        return node, new_delay
    
    def process_children(self, node):
        """Creates and submits tasks for children of a node."""
        crawl_delay = self.rules.crawl_delay
        for child in node.children:
            task = self.create_task(child, crawl_delay)
            self.app.tasks_made +=1
            self.submit_task(task, child.url)

    def daemon_shutdown(self):
        """Shut down uvicorn web server when job is complete."""
        task_id = "shutdown"
        command_line = f"{COMMAND_LINE_PATH}/shutdown.py"
        task = batch_models.TaskAddParameter(id=task_id, command_line=command_line)
        self.batch_client.task.add(self.job_id, task)
    
    def check_if_finished(self, start_time):
        """Polls self.future periodically to see if there are any tasks left to process, 
            and shuts down daemon if none are found."""
        all_done = all(f.done() for f in list(self.futures))

        if all_done:
            job_end_time = time.time()
            print(f"Job took {job_end_time - start_time} seconds. Processed {len(self.seen)}, Tasks made = {self.tasks_made}, final crawl delay: {self.rules.crawl_delay}")
            self.daemon_shutdown()
            self.executor.shutdown(wait=False)

        else:
            self.app.after(500, self.check_if_finished, start_time)

    def update_crawl_delay(self, new_delay, crawl_delay):
        """This function ensures that if multiple workers with the same crawl_delay value 
        need to increase the delay, that this only updates the user agent rules once."""

        if new_delay > crawl_delay:
            current_delay = self.rules.crawl_delay
            with self.lock:
                if current_delay == crawl_delay:
                    self.rules.crawl_delay = new_delay