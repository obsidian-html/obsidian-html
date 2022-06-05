function toggle_dir(dir_button_id){
    id = dir_button_id.split('-')[1]
    cont = document.getElementById('folder-container-'+id)
    return toggle(cont)
}