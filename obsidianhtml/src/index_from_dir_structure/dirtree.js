function toggle_dir(dir_button_id){
    console.log(dir_button_id);
    id = dir_button_id.split('-')[1]
    cont = document.getElementById('folder-container-'+id)

    if (cont.style.display == "block") {
            cont.style.display = "none";
    }
    else {
            cont.style.display = "block";
    }
}