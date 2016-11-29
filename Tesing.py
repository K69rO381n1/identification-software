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