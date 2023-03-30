//global variables
let data_objects = [];
let data_file_names = [];

document.addEventListener("DOMContentLoaded", function (){
    $("#json_file").change(function(){
        for(let i=0; i<this.files.length; i++){
            let reader = new FileReader();
            let tmp = this;

            reader.onload = function(e){

                let data = JSON.parse(e.target.result);
                let keys = Object.keys(data);

                if(typeof data[keys[0]]["_image"] === "string" && typeof data[keys[1]]["_image"] === "string")
                    return;

                data_objects.push(data);
                data_file_names.push(tmp.files[i].name);

                if (i === tmp.files.length - 1)
                    build_forms();
            }

            reader.readAsText(this.files[i])
        }

        $(this).parent().parent().hide();
    })

    $("#json_textarea").change(function(){
        try {
            let data = JSON.parse($(this).val());
            let keys = Object.keys(data);
            data_objects.push(data);
            data_file_names.push(keys[0] +" vs "+ keys[1] +".json");

            $("#textarea_info").text("(inserted "+ data_objects.length +" datasets)");
            $(this).val("");
            $("#cfg_inserted_datasets_btn:hidden").show()
        }
        catch(e){
            //nothing here
        }
    })
})

$("#cfg_inserted_datasets_btn").click(function(e){
    e.preventDefault();
    build_forms();
    $(this).parent().hide();
})

$(document).on("change", "#forms_container input[type=file]", function (){
    let is_ready_to_download = false;

    for(let i=0; i<data_objects.length; i++){
        if(document.getElementById("img_a_"+i).files.length && document.getElementById("img_b_"+i).files.length){
            is_ready_to_download = true;
        }
    }

    $("#download_btn").toggleClass("disabled", !is_ready_to_download)
})


$("#download_btn").click(async function(e){
    e.preventDefault();

    // use a BlobWriter to store with a ZipWriter the zip into a Blob object
    const blobWriter = new zip.BlobWriter("application/zip");
    const writer = new zip.ZipWriter(blobWriter);


    for(let i=0; i<data_objects.length; i++){
        let input_a = document.getElementById("img_a_"+i);
        let input_b = document.getElementById("img_b_"+i);
        if(input_a.files.length && input_b.files.length){
            let keys = Object.keys(data_objects[i])
            data_objects[i][keys[0]]["_image"] = input_a.files[0].name;
            data_objects[i][keys[1]]["_image"] = input_b.files[0].name;

            await writer.add(data_file_names[i], new zip.TextReader(JSON.stringify(data_objects[i])));
            $(input_a).closest(".form-item").remove();
        }
    }

    // close the ZipReader
    await writer.close();

    // get the zip file as a Blob
    const blob = await blobWriter.getData();
    $("<a href='"+ URL.createObjectURL(blob) +"' download='Data files'></a>")[0].click()
})


function build_forms(){
    let $container = $("#forms_container");

    data_objects.forEach(function(data, index){
        let keys = Object.keys(data)

        let $info = $('<div class="text-secondary">'+ data_file_names[index] +'</div>');
        let $input_a = $('<div class="mb-3 mt-2">' +
            '<label for="json_file" class="form-label fw-bold">'+ keys[0] +'</label>' +
            '<input class="form-control" type="file" id="img_a_'+ index +'" accept="image/png, image/jpg, image/jpeg">' +
            '</div>')
        let $input_b = $('<div class="mb-3 mt-2">' +
            '<label for="json_file" class="form-label fw-bold">'+ keys[1] +'</label>' +
            '<input class="form-control" type="file" id="img_b_'+ index +'" accept="image/png, image/jpg, image/jpeg">' +
            '</div>')

        let $inner_container = $('<div class="shadow mt-5 p-2 border rounded form-item"></div>');
        $inner_container.append($info, $input_a, $input_b);
        $container.append($inner_container)
        $("#action_container").show();
    })
}