# Get returncode of previous command   
   
In Powershell:   
``` powershell
python bla.py

# Return code == 0
if ($?){
	Write-Host "Success"
}
# Return code != 0
if (-not $?){
	Write-Host ":("
}
```