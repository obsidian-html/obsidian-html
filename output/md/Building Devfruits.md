# Building Devfruits   
This website started when I read about [Smart note taking](Private/Education/Smart%20note%20taking.md) and decided to try out [Obsidian](Private/Obsidian/Obsidian.md). I really enjoy the way this system works for making notes. It's a very fluent way of working. Note taking should be quick and painless in my opinion.   
   
> It might be clear that this website's design is heavily inspired by [this website](https://notes.andymatuschak.org/Evergreen_notes). And actually, I'm still planning on stealing it's click-through dynamic. Can't improve on perfect, and that website is perfection in my book. **Edit** Okay I stole that too now.   
   
## But wait, there's more   
Something that might happen when you make a web of notes, is the desire to share these notes with others, but Obsidian doesn't make this easy:   
   
- First off, Obsidian uses non-standard markdown in its files. This is part of what makes working with Obsidian so fluent: Obsidian does a lot of work for you.    
- Secondly: [publishing your notes via Obsidian](https://obsidian.md/publish) costs **20 dollar per month**. And no self-hosted option is available.    
- Thirdly: no code is available to convert Obsidian code to proper markdown.   
   
## The solution   
So, the challenge was to [write some code that can convert an Obsidian note folder to proper markdown](https://bit.ly/3DzKmmn), and then convert that markdown to html. For the latter part we can use [Python-Markdown](https://python-markdown.github.io/).   
   
## Press of a button publish experience   
Then, to make the experience really seamless, I made a Powershell function that will run the code above and then push it to my local webserver.    
   
The function lives in my personal Powershell module, so I can call it directly after opening any Powershell console. It looks like this:   
   
``` powershell   
Function Publish-Obsidian {   
    param(   
        $Entrypoint = "C:\Users\User\OneDrive\Obsidian\Notes\Devfruits Notes.md",    
        $RootFolder = "C:\Users\User\OneDrive\Obsidian\Notes\",    
        $PrivateKeyPath = $script:PrivateKeyPath   
    )   
   
    # NOTE: first install obsidian-html in C:\Users\User\Documents\git\obsidian-html   
   
    # Convert Obsidian to HTML   
    $origin = pwd   
    cd  'C:\Users\User\Documents\git\obsidian-html'   
    python run.py $RootFolder $Entrypoint   
    cd $origin   
   
    # Delete files on the server   
    [System.IO.File]::WriteAllLines("$($env:TEMP)\_emptydevfruits.sh", "rm -rf /home/user/www/devfruits/*")   
    plink -batch -i $PrivateKeyPath user@web001 -m "$($env:TEMP)\_emptydevfruits.sh"   
   
    # Upload files   
    pscp -r -i $PrivateKeyPath C:\Users\User\Documents\git\obsidian-html\output\html\* user@web001:/home/user/www/devfruits/   
}   
```   
   
## Thoughts on this way of working   
One nice thing about the Python code that I wrote is that it crawls through the notes based on links. So as long as I don't link (directly or indirectly) between my entrypoint note used for this site, and any random notes that also live in my note's folder, they won't show up on this website.    
   
This allows me to keep Obsidian always open and not switch between folders when I quickly want to add a note on the website, or in my personal dossier.    
   
Of course, this is very prone to publishing personal notes, but I have no creditcard information in my notes, so other than sharing something cringey, I don't see a lot of risk there. Also: the graph view allows me to see which note-clouds are seperated from each other, so that's a nice visual double-check.   
   
The publish experience is, as I said, seamless, and takes about 5 seconds, with the amount of notes that I have at the time of writing, to compile and upload to my server . No log ins, no git clone, no remembering commands, no content-management systems. Just write your notes in finely tuned note-taking app, and call `Publish-Obsidian`.    
   
Comfortable!