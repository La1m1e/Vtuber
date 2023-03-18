from configparser import ConfigParser
import cv2
import pyaudio
import numpy as np
import configparser
import os
import ctypes
import time
import sys
# ///////////////////////////////////////////
debugMode = False
# ///////////////////////////////////////////

config: ConfigParser = configparser.ConfigParser()
DEFAULT_WIDTH = '700'
DEFAULT_HEIGHT = '700'
DEFAULT_SENS = '350'  # importing default settings
DEFAULT_LOUD = '5'  # value multiplier for loud.png
prev_value = None  # just for rewriting the config file in case slider is moved
start = 0
end = 0
config.comment_prefixes = ';'
if not os.path.exists('img'):
    os.makedirs('img')

if not os.path.isfile('readme.txt'):
    # Open a file for writing
    with open("readme.txt", "w") as f:
        f.write("Поместите три файла silent.png, speak.png и loud.png соответственно их названиям в папку img \n")
        f.write("Размеры окна, а так же значение во сколько раз громче должен быть порог активации для loud.png можно "
                "настроить в файле config.cfg\n")
        f.write('\n')
        f.write("Place three files silent.png, speak.png and Loud.png in the img folder \n")
        f.write("The size of the window, as well as the value of how many times louder the activation threshold for "
                "loud.png can be configured in the config.cfg file \n")


def read():  # reading from config function with ValueError exception
    try:
        config.read('config.cfg')
        windowWidth = int(config.get('DEFAULT', 'Width', fallback=DEFAULT_WIDTH))
        windowHeight = int(config.get('DEFAULT', 'Height', fallback=DEFAULT_HEIGHT))
        sliderValue = int(config.get('DEFAULT', 'Sensitivity', fallback=DEFAULT_SENS))
        loud_multiplier = int(config.get('DEFAULT', 'Loud_multiplier', fallback=DEFAULT_LOUD))
        return windowWidth, windowHeight, sliderValue, loud_multiplier
    except ValueError:
        ErrorBox = ctypes.windll.user32.MessageBoxW
        ErrorBox(None,
                 'Неверная конфигурация. Проверьте config.cfg на наличие переменных неверного типа. '
                 'Напоминаем, все значения должны быть указанны в виде натуральных чисел. '
                 '\nInvalid configuration. Check config.cfg for variables of the wrong type. '
                 'We remind you that all values must be specified as natural numbers.', 'ERROR!', 0)
        sys.exit(1)


if not os.path.exists('config.cfg'):  # checking for an existing config file, if not - create default one
    config['DEFAULT'] = {'Width': DEFAULT_WIDTH, 'Height': DEFAULT_HEIGHT,
                         'Sensitivity': DEFAULT_SENS, 'Loud_multiplier': DEFAULT_LOUD}

    with open('config.cfg', 'w') as configfile:
        config.write(configfile)
    width, height, value, loud = read()
else:
    width, height, value, loud = read()
del (DEFAULT_WIDTH, DEFAULT_HEIGHT, DEFAULT_SENS, DEFAULT_LOUD)  # delete default values from memory

silence_img = cv2.imread("img/silent.png")
speak_img = cv2.imread("img/speaking.png")  # loading images
loud_img = cv2.imread("img/loud.png")

pa = pyaudio.PyAudio()  # starting up the mic listening
stream = pa.open(format=pyaudio.paInt16,
                 channels=1,
                 rate=44100,
                 input=True,
                 frames_per_buffer=1024)

# Set up the GUI
cv2.namedWindow("VCam")
cv2.createTrackbar("Sensitivity", "VCam", value, 10000, lambda x: None)  # create slider with cfg value

while True:  # main cycle
    data = np.frombuffer(stream.read(1024), dtype=np.int16)  # current microphone level
    level = np.abs(data).mean()
    try:
        value = cv2.getTrackbarPos("Sensitivity", "VCam")  # quit in case getpos returns an error
    except:  # Happens when the window is being closed with X
        sys.exit(1)  # but the While True: is still running causing an error
    # ////////////////////////////////////////////
    if debugMode:
        print("MicLevel = ", level)
        print("SpeakingValue = ", value)
        print("ShoutingValue = ", value * loud)
        end = time.time()  # stop debugging timer
        print("Execution time: ", end - start)  # get execution time
        start = time.time()  # start debugging timer
    # ////////////////////////////////////////////
    if level < value:
        img = silence_img
    elif level < value * loud:  # setting the image for the current cycle and loudness
        img = speak_img
    else:
        img = loud_img
    try:
        img = cv2.resize(img, (width, height))  # displaying an image with an exception with fix suggestions
        cv2.imshow("VCam", img)
    except cv2.error:
        Error = ctypes.windll.user32.MessageBoxW
        Error(None,
              'Поместите файлы silent.png, speaking.png и loud.png в dir/img/ для продолжения работы.'
              '\nPlace Silent.png, Speaking.png and Loud.png files in dir/img/ folder.', 'ERROR!', 0)
        sys.exit(1)

    if value != prev_value:
        config['DEFAULT'] = {'Width': width, 'Height': height,
                             'Sensitivity': value, 'Loud_multiplier': loud}  # Rewriting new slider value
        with open('config.cfg', 'w') as configfile:
            config.write(configfile)
        prev_value = value

    key = cv2.waitKey(1)
    if key == ord("p"):
        break
