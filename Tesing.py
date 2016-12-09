# # from captcha.audio import AudioCaptcha
# from captcha.image import ImageCaptcha
# from os import listdir
#
# FONTS_DIR = "data/font/"
# VOICES_DIR = "data/voice/"
# FONTS = [FONTS_DIR+font for font in listdir(FONTS_DIR)]
#
# # audio = AudioCaptcha(voicedir='data/voice')
# image = ImageCaptcha(fonts=FONTS)
#
# # data = audio.generate('111')
# # audio.write('111', 'out.mp3')
#
# data = image.generate('H a l l o   w o r l d')
# print(data.read())
# image.write('H a l l o   w o r l d', 'out.png', format='png')
