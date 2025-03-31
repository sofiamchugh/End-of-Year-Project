import json
def load_config():
    with open('config.json') as f:
        config = json.load(f)
    return config

config = load_config()

command = f"""C:\Windows\System32\cmd.exe /c ( echo starting
&& az storage blob download --account-name {config["storage-account-name"]} --container-name repo --name worker.py --file D:\\batch\\repo\\worker.py
&& echo in progress)"""


"""&&
        az storage blob download --account-name {config["storage-account-name"]} --container-name repo --name main.py --file D:\\batch\\repo\\main.py &&
        az storage blob download --account-name {config["storage-account-name"]} --container-name repo --name gather.py --file D:\\batch\\repo\\gather.py &&
        az storage blob download --account-name {config["storage-account-name"]} --container-name repo --name config.json --file D:\\batch\\repo\\config.json &&
        az storage blob download --account-name {config["storage-account-name"]} --container-name repo --name azure_config.py --file D:\\batch\\repo\\azure_config.py &&
        python D:\\batch\\repo\\worker.py && echo I did it \n"""