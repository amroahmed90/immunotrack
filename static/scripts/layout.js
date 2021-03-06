// a function that styles the active nav link to indicate the current page
function style_active_link(active_index) {
	//removing the current active page
	var nav_links = document.getElementsByTagName('li');
	for (var i = 0; i < nav_links.length; i++)
	{
		nav_links[i].classList.remove("active")
	}
    nav_links[active_index].classList.add("active")
}