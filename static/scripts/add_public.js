function show_hide_block(radio_id, div_id) {
    var div_element = document.getElementById(div_id);
    var radio_element = document.getElementById(radio_id);
    if (radio_element.checked) {
        div_element.style.display = 'block';
    }
    else div_element.style.display = 'none';
}