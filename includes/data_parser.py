import json
import os
import glob
import re

absolute_path = os.path.dirname(__file__)
relative_path = "../data_single/"
target_path = os.path.join(absolute_path, relative_path)

#example: save_single_data("Country", "Austria", json_object)
def save_single_data(category, entity_name, data_json, create_versus_files = True):

    path = target_path + category +"/"+ entity_name +".json"
    
    if(not os.path.isdir(target_path + category)):
        os.mkdir(target_path + category)

    if(os.path.isfile(path)):
        print(path + " already exists.\nNOT CHANGED")
        return False

    #creating versus files
    other_single_data_paths = glob.glob(target_path + category +"/*.json")
    for other_data_path in other_single_data_paths:
        re_result = re.search('.+\\\(.+)\.json$', other_data_path)
        other_entity_name = re_result.group(1)
        other_data = json.load(open(other_data_path, encoding="utf-8"))
        json.dump({
            entity_name: data_json,
            other_entity_name: other_data
        }, open(os.path.join(absolute_path, "../data/") + entity_name +" vs "+ other_entity_name +".json", 'x'))
        

    #writing single data to disk
    f = open(path, "x")
    f.write(json.dumps(data_json))
    print(path +" was saved successfully.")
    return True