# Markdown link regex
## Test of this page
Mostly manual still, still need to write a regression test.

See if these links are all rendered correctly:

md link with parentheses around it([note --> html](../../General%20Information/Snippets/note%20--%3E%20html.md)).  
md link with parentheses in it [note --> html](../../General%20Information/Snippets/note%20--%3E%20html.md).   
both ([note --> html](../../General%20Information/Snippets/note-(bla).md)).

again, followed by (bla)

md link with parentheses around it([note --> html](../../General%20Information/Snippets/note%20--%3E%20html.md)).  (bla) 
md link with parentheses in it [note --> html](../../General%20Information/Snippets/note%20--%3E%20html.md).   (bla)
both ([note --> html](../../General%20Information/Snippets/note-(bla).md)). (bla)
   

without dot

md link with parentheses around it([note --> html](../../General%20Information/Snippets/note%20--%3E%20html.md)) 
md link with parentheses in it [note --> html](../../General%20Information/Snippets/note%20--%3E%20html.md)   
both ([note --> html](../../General%20Information/Snippets/note-(bla).md))

md link with parentheses around it([note --> html](../../General%20Information/Snippets/note%20--%3E%20html.md))  (bla)
md link with parentheses in it [note --> html](../../General%20Information/Snippets/note%20--%3E%20html.md)   (bla)
both ([note --> html](../../General%20Information/Snippets/note-(bla).md)) (bla)

image links with parentheses:

`![[name(withpars).png]]`

![[name(withpars).png]]

`![name(withpars).png](name(withpars).png)`

![name(withpars).png](name(withpars).png)

`![[name (with pars and spaces).png]]`

![[name (with pars and spaces).png]]

`![[name with spaces.png]]`

![[name with spaces.png]]

## Next test
