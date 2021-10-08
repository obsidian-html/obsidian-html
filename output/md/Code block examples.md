# Code block examples   
I use this note to test the stylesheet that I'm formatting for this website I use this note to test the stylesheet that I'm formatting for this website   
   
## Python   
``` python   
import sys 					# commandline arguments   
import shutil 				# used to remove a non-empty directory, copy files   
import re 					# regex string finding/replacing   
from pathlib import Path 	#    
import frontmatter 			# remove yaml frontmatter from md files   
import markdown 			# convert markdown to html   
import urllib.parse 		# convert link characters like %   
   
# python run.py 'C:\Users\Installer\OneDrive\Obsidian\Notes' 'C:\Users\Installer\OneDrive\Obsidian\Notes\Work.md'   
     
# Input   
# ------------------------------------------   
root_folder = sys.argv[1] 	# first folder that contains all markdown files   
entrypoint = sys.argv[2] 	# The note that will be used as the index.html   
   
if root_folder[-1] == '\\':   
 root_folder = root_folder[:-1]   
```   
   
``` python   
# -- CLIENT SETUP --------------------------------------------------------------------   
# ====================================================================================   
load_dotenv()   
TOKEN = os.getenv('DISCORD_TOKEN')   
   
intents = discord.Intents.default()   
intents.members = True   
   
client = discord.Client(intents=intents)      
   
# -- MESSAGE EVENT -------------------------------------------------------------------   
# ====================================================================================   
@client.event   
async def on_message(message):   
    # Init   
    now = datetime.now() # current date and time   
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")   
   
    # Don't respond to self to avoid endless loops   
    if message.author == client.user:   
        return   
```   
   
   
## Powershell   
```powershell   
Function Add-Link {   
    param(   
        $Link,    
        $Title,   
        $Description,   
        $Category = 'misc',   
        $PrivateKeyPath = $script:PrivateKeyPath           
    )   
   
    # Compile script to be run on the linux host   
    $script = "cd /home/user/www/devfruits/links`n"   
    $script += "python3 add.py '$Category' '$Link' '$Title' '$Description'`n"   
    $script += "python3 publish.py"   
    [System.IO.File]::WriteAllLines("$($env:TEMP)\_addlink.sh", $script)   
   
    # Run script   
    plink -batch -i $PrivateKeyPath user@web002 -m "$($env:TEMP)\_addlink.sh"   
}   
```   
   
## YAML   
``` yaml   
---   
# This is a basic workflow to help you get started with Actions   
   
name: CI   
   
# Controls when the action will run.    
on:   
  # Triggers the workflow on push or pull request events but only for the main branch   
  push:   
    branches: [ main ]   
  pull_request:   
    branches: [ main ]   
   
  # Allows you to run this workflow manually from the Actions tab   
  workflow_dispatch:   
   
# A workflow run is made up of one or more jobs that can run sequentially or in parallel   
jobs:   
  # This workflow contains a single job called "build"   
  build:   
    # The type of runner that the job will run on   
    runs-on: self-hosted   
   
    # Steps represent a sequence of tasks that will be executed as part of the job   
    steps:   
      # Checks-out your repository under $GITHUB_WORKSPACE, so your job can access it   
      - uses: actions/checkout@v2   
   
      # Runs a single command using the runners shell   
      - name: Run a one-line script   
        run: echo Hello, world!   
   
      # Runs a set of commands using the runners shell   
      - name: Run a multi-line script   
        run: |   
          echo "$HOSTNAME"   
          touch /home/github/testttttt   
          pwd   
```   
   
## Bash   
``` bash   
    # Set rights   
    # ---------------------------   
    # Create www-data group, and add main user to it   
    if [ $setWWWData -eq 1 ](/not_created.md);   
    then   
        sudo groupadd www-data   
        sudo usermod $mainUser -a -G www-data   
   
        # Give www-data rights to everything in /var/www/   
        sudo chown -R :www-data /var/www/   
    fi   
   
    # Empty default site block   
    # ---------------------------   
    if [ $distro -eq $MANJARO ](/not_created.md);   
    then   
        sudo touch /etc/nginx/sites-available/default   
           
    elif [ $distro -eq $UBUNTU ](/not_created.md);   
    then   
        sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/_default_factory   
        sudo echo "" > /etc/nginx/sites-available/default   
    fi       
```