from moviepy.editor import *
from moviepy.video.fx import lum_contrast
from includes import custom_resize
import json
import glob
import sys
import random

print("Starting...")

sys.setrecursionlimit(4000) #update when neccesary but be careful

#global variables
vignette_clip = None

def create_intro_clip(title_a = "Undefined", title_b = "Undefined"):
    clip = VideoFileClip("video/intro_background.mp4")
    text_clip = TextClip(title_a +"\n\nvs\n\n"+ title_b, color="white", font="Typewriter", kerning = 5, fontsize=120).set_pos("center").set_duration(clip.duration)
    return CompositeVideoClip([clip, text_clip])

def create_img_clip(img, title = "Undefined", label = "Undefined", value = "Undefined"):
    clip = ImageClip(img).set_duration(3).fx(lum_contrast.lum_contrast, -20, 0.2).resize(lambda t: 1 + 0.04 * t).set_position(("center", "center"))
    text_clip = TextClip(title +"\n\n"+ label +"\n\n"+ value, color="white", font="Ubuntu", kerning = 5, fontsize=100, stroke_color="black", stroke_width=5).set_pos("center").set_duration(clip.duration)
    return CompositeVideoClip([clip, text_clip])

def find_sound_peaks(sound_array, duration, audio_fps, callback_function):
    index = 0
    array_length = len(sound_array)
    last_start_index = None
    previous = [0.1]
    for sound_array_item in sound_array:
        val = (sound_array_item[0] + sound_array_item[1]) / 2

        if(val < 0):
            val *= -1
        if(val > (sum(previous) / len(previous)) * 4.5):
            if(not last_start_index):
                last_start_index = index
        else:
            if(last_start_index):
                start_relative_pos = last_start_index / array_length
                end_relative_pos = index / array_length
                if(end_relative_pos - start_relative_pos > 0.01): #TODO: replace to be a variable
                    #print(last_start_index, index, start_relative_pos, end_relative_pos)
                    callback_function(last_start_index / array_length * duration, index / array_length * duration)
                    last_start_index = None   

        previous.append(val)

        if(len(previous) > 100):
            previous.pop(0)

        index += 1

    return

def create_video(json_path):
    global vignette_clip
    json_file = open(json_path, encoding="utf-8")
    data = json.load(json_file)

    clips = []

    key_a = list(data.keys())[0]
    key_b = list(data.keys())[1]

    print("Processing "+ key_a +" vs "+ key_b)

    clips.append(create_intro_clip(key_a, key_b))

    props = list(data[key_a].keys())
    props.remove("_labels")
    props.remove("_image")

    for index in range(len(props)):
        clips.append(create_img_clip("images/"+data[key_a]["_image"], key_a, data[key_a]["_labels"][index], data[key_a][props[index]]))
        clips.append(create_img_clip("images/"+data[key_b]["_image"], key_b, data[key_b]["_labels"][index], data[key_b][props[index]]))

    full_clip = concatenate_videoclips(clips)
    full_clip = full_clip.set_start(0, False).set_start(0).set_end(full_clip.duration)
    audio_fps = 44100
    audio_file_paths = glob.glob("music/*.mp3")
    audio = AudioFileClip(random.choice(audio_file_paths), fps = audio_fps).subclip(0, full_clip.duration)
    #audio = AudioFileClip("music/Waste.mp3", fps = audio_fps).subclip(0, full_clip.duration)

    #process sound array
    sound_array = audio.to_soundarray()

    vignette_clip = ImageClip("image_components/vignette.png").set_duration(full_clip.duration)


    def sound_peak_callback(t_start, t_end):
        global vignette_clip
        t_middle = t_start + (t_end - t_start) / 2
        #print(t_start, t_end)
        vignette_clip = vignette_clip.subfx(custom_resize.custom_upsize, t_start, t_middle).set_position("center", "center")
        vignette_clip = vignette_clip.subfx(custom_resize.custom_downsize, t_middle, t_end).set_position("center", "center")
        return

    find_sound_peaks(sound_array, audio.duration, audio_fps, sound_peak_callback)

    full_clip = CompositeVideoClip([full_clip, vignette_clip])
    full_clip.audio = audio

    #append subscribe video
    full_clip = concatenate_videoclips([full_clip, VideoFileClip("video/subscribe.mp4")])

    #writing to disk
    full_clip.write_videofile("output/"+ json_path.replace(".json", "").replace("data\\", "") +".mp4", 30, "libx264")




#reading input
data_files = glob.glob("data/*.json")
output_files = glob.glob("output/*.mp4") + glob.glob("output_uploaded/*.mp4")

for output_file in output_files:
    data_path = output_file.replace(".mp4", ".json").replace("output\\", "data\\").replace("output_uploaded\\", "data\\")
    if(data_path in data_files):
        data_files.remove(data_path)

#random shuffle to prevent boring sequence
random.shuffle(data_files)

created_count = 0

for data_file in data_files:
    create_video(data_file)
    created_count += 1

print("Finished ("+ str(created_count) +" media was created)")
