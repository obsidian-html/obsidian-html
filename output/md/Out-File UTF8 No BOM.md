# Out-File UTF8 No BOM   
   
Use    
``` powershell
[System.IO.File]::WriteAllLines($MyPath, $MyRawString)
```   
   
Instead of Out-File, this defaults to UTF8 - no BOM