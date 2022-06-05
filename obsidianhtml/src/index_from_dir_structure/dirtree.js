function toggle_dir(dir_button_id){
    console.log(dir_button_id);
    id = dir_button_id.split('-')[1]
    cont = document.getElementById('folder-container-'+id)

    if (cont.classList.contains("active")) {
        cont.classList.remove("active")
    } else {
        cont.classList.add("active")
    }
}