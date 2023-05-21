function move_dirtree_list_item_into_view(){
    // Scroll dirtree to current note
    let scrollElement = document.querySelector(".current_page_dirtree");
    scrollElement.scrollIntoView({ block: "center" });
}
document.addEventListener('DOMContentLoaded', move_dirtree_list_item_into_view);


function toggle_dir(dir_button_id){
    // set active on dir_button, this only applies the icon (open close folder svg)
    let dir_button = document.getElementById(dir_button_id)
    if (dir_button.classList.contains("active")){
        dir_button.classList.remove("active")
    } else {
        dir_button.classList.add("active")
    }

    // actually show contents
    id = dir_button_id.split('-')[1]
    cont = document.getElementById('folder-container-'+id)
    return toggle(cont)
}

function open_folder_note(el){
    url = el.getAttribute('href')
    window.location.href = url;
    return false;
}