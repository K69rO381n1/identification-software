import os

import shutil


def _create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)


def _move_loc(old_path, new_path):
    shutil.move(old_path, new_path)


def _change_type(file_path):
    pre, ext = os.path.splitext(file_path)
    os.rename(file_path, pre + ".wav")


def convert_audio_file_to_wav_and_put_them_in_folder(path):
    for ascii_num in list(range(66, 91))+list(range(48, 58)):
        char = chr(ascii_num)
        file_path = path + "/" + str(char)
    
        _create_folder(file_path)
        _change_type(file_path+".mp3")
        _move_loc(file_path+".wav", file_path+"/"+char+".wav")


if __name__ == '__main__':
    father_path = r"/home/kfir/Documents/identification_software-Server_side/data/voice"
    convert_audio_file_to_wav_and_put_them_in_folder(father_path)
