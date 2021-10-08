# Error: The underlying connection was closed: An unexpected error occurred on a receive   
   
Happens with [Invoke-Restmethod](/not_created.md) and can be fixed by enforcing the use of TLS1.2:   
``` powershell
[Net.ServicePointManager]::SecurityProtocol =[Net.SecurityProtocolType]::Tls12
```