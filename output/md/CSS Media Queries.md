# CSS Media Queries   
With media queries we can change the way the page is formatted based on the properties of the device.    
   
The most used option is to change the layout for mobile devices, where the screen space is too limited to allow for the sprawling layouts that we can afford on desktops:   
   
``` css
@media (min-width: 800 px) {
	.container {
		float: none;
	}
}
```   
   
   
Read more about media queries on [MDN: Using media queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Media_Queries/Using_media_queries).