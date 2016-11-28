# from captcha.audio import AudioCaptcha
from captcha.image import ImageCaptcha

# audio = AudioCaptcha(voicedir='data/voice')
image = ImageCaptcha(fonts=['data/font/DroidSansMono.ttf',
                            'data/font/SEASRN__.ttf',
                            'data/font/FFF_Tusj.ttf',
                            'data/font/CaviarDreams.ttf',
                            'data/font/Capture_it.ttf',
                            'data/font/Amatic-Bold.ttf'])

# data = audio.generate('111')
# audio.write('111', 'out.mp3')

data = image.generate('Hallo world')
image.write('Hallo world', 'out.bmp', format='bmp')

# import os
#
# import shutil
#
#
# def create_folder(path):
#     if not os.path.exists(path):
#         os.makedirs(path)
#
#
# def move_loc(old_path, new_path):
#     shutil.move(old_path, new_path)
#
#
# def change_type(file_path):
#     pre, ext = os.path.splitext(file_path)
#     os.rename(file_path, pre + ".wav")
#
#
#
#
# father_path = r"/home/kfir/Documents/identification_software-Server_side/data/voice"
#
# for ascii_num in list(range(66, 91))+list(range(48, 58)):
#     char = chr(ascii_num)
#     file_path = father_path + "/" + str(char)
#
#     create_folder(file_path)
#     change_type(file_path+".mp3")
#     move_loc(file_path+".wav", file_path+"/"+char+".wav")