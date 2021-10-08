# HTTP requests in Python   
Before installing pip packages, be sure to enable a venv: [Using Venvs](Using%20Venvs.md).   
   
## Install prerequisites   
``` bash
pip install requests
```   
   
> If you are behind a proxy, you might need to [configure pip to work with a proxy](Pip%20behind%20a%20proxy.md).   
   
# Get requests   
## Example scripts   
``` python
import requests

headers = {'Content-Type': 'application/json; charset=utf-8', 'Authorization': 'Splunk eyJraWQiOiJzc.blablalba.tartradfpdnhfpl'}

response = requests.get("https://api.splunk.intranet.rws.nl/servicesNS/-/RWS-IRI/data/ui/views/cnap__smoketest_environment_details?output_mode=json", headers=headers, verify=False)

print(response.text)
```   
   
   
   
   
# Related   
[HTTP Requests](HTTP%20Requests.md)