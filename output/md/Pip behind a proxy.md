# Pip behind a proxy   
   
Create or edit the [pip.ini](pip.ini.md) file to contain the following:   
   
``` ini   
[global]    
trusted-host =  pypi.python.org    
				pypi.org    
				files.pythonhosted.org    
proxy = [http://webproxy.rws.nl:8080/](http://webproxy.rws.nl:8080/)   
```   
   
If you are on Linux, don't forget to point to the pip.ini file, if not yet done:   
``` bash   
export PIP_CONFIG_FILE=/path/to/pip.ini   
```