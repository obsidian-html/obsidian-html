# Local Git Configuration   
Configuring git users and ssh key authentication is a [Recurring Configuration Task](/not_created.md), and one of the first steps of [Setting up a new workspace](Setting%20up%20a%20new%20workspace.md).    
   
## Avoid Global settings   
If you work with multiple git users, and need to use different ssh keys, the best option is to not set global configurations at all. This way you will always be warned when you haven't set your local git config, and this avoids the risk of using the wrong user when committing and pushing.   
   
## Setting local config   
- Open the local git config file, e.g. `/git/myrepo/.git/config`   
- Add the following line under `[core]`:   
  ```   
  sshCommand = "ssh -i ~/.ssh/<your ssh key file>"   
  ```   
- Add the following lines under `[user]`:   
  ```   
  email = <your email>   
  name = <your name>   
  ```   
   
## Test config   
Run `git config user.name` to test what the actual settings are   
   
# Troubleshooting   
## Wrong user used on git push   
This is often a problem with the configured ssh key not being loaded.   
   
``` bash   
# Open bash with ssh-agent active   
exec ssh-agent bash   
   
# Add ssh key to agent   
ssh-add ~/.ssh/<key>   
```   
   
## SSH key is not being not used   
- Check if the remote origin link uses a git link, like:   
   `git remote add origin git@github.com:dwrolvink/obsidian-html.git`   
   
   
# References   
- [https://dev.to/web3coach/how-to-configure-a-local-git-repository-to-use-a-specific-ssh-key-4aml](https://dev.to/web3coach/how-to-configure-a-local-git-repository-to-use-a-specific-ssh-key-4aml)