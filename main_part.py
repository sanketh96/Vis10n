import requests
import cv2
import numpy as np
import math
import os
import time
import shutil
from gtts import gTTS
import matplotlib.pyplot as plt
import subprocess
import pickle
import speech_recognition as sr
import pickle
import threading
import logging
from collections import OrderedDict

cwd = os.getcwd()
frame_dir = "Frames"
frame_num = 64

to_search = {"valid": False, "word" : None}

_region = 'westcentralus' #Here you enter the region of your subscription
_url = 'https://{}.api.cognitive.microsoft.com/vision/v1.0/analyze'.format(_region)
_key = "1521c4187fad4ce1b6b92d5b8559f33c"
_maxNumRetries = 10

headers = dict()
headers['Ocp-Apim-Subscription-Key'] = _key
headers['Content-Type'] = 'application/octet-stream'

params   = {'visualFeatures': 'Categories,Description,Color,Tags'}

thread_data = {}

objects = []
detected = False

path = os.path.join(cwd, frame_dir)


def create_thread(thread_name, filename):
    threading.Thread(target = process_image, args = (thread_name, filename)).start()

def get_the_search_word():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak:")
        audio = r.listen(source)
    try:
        to_search["valid"] = True
        word = r.recognize_google(audio)
        to_search["word"] = (word.lower())
        print("Word = ", word)
    except sr.UnknownValueError:
        print("Could not understand audio")
        to_search["valid"] = False
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
        to_search["valid"] = False

def generate_new_frame_name():
    global frame_num
    frame_num += 1
    return("frame_"+chr(frame_num)+".png")

def generate_frames():
    # Display the resulting frame
    speak("Start scanning surrounding left to right")
    count = 0
    while(1):
        cap = cv2.VideoCapture("https://192.168.1.5:8080/video") # replace the argument to 0 to use laptop webcam
        ret, frame = cap.read()
        speak("pause")
        time.sleep(500/1000.0)
        frame_name = generate_new_frame_name()
        cv2.imwrite(os.path.join(path, frame_name), frame)
        count += 1
        speak("scan")
        create_thread("Thread" + str(count), frame_name)
        time.sleep(500/1000.0)
        if(check_for_object()):
            speak("Object detected")
            break
            cap.release()
        if(count == 7):
            break
            cap.release()

        cap.release()


def check_for_object():
    global objects
    objects = list(map(lambda x: x.lower(), objects))
    if(to_search["word"] in objects):
        return True
    return False

def processRequest( json, data, headers, params ):
    retries = 0
    result = None

    while True:
        response = requests.request( 'post', _url, json = json, data = data, headers = headers, params = params )

        if(response.status_code == 429):

            print("Message: %s" % ( response.json() ))

            if(retries <= _maxNumRetries):
                time.sleep(1)
                retries += 1
                continue
            else:
                print('Error: failed after retrying!')
                break

        elif ((response.status_code == 200) or (response.status_code == 201)):

            if(('content-length' in response.headers) and (int(response.headers['content-length']) == 0)):
                result = None
            elif(('content-type' in response.headers) and (isinstance(response.headers['content-type'], str))):
                if('application/json' in response.headers['content-type'].lower()):
                    result = response.json() if response.content else None
                elif('image' in response.headers['content-type'].lower()):
                    result = response.content
        else:
            print("Error code: %d" % ( response.status_code ))
            print("Message: %s" % (response.json()))

        break
    return result

def speak(text):
    # This module is imported so that we can
    # play the converted audio
    mytext = text
    language = 'en'

    # Passing the text and language to the engine,
    # here we have marked slow=False. Which tells
    # the module that the converted audio should
    # have a high speed
    myobj = gTTS(text=mytext, lang=language, slow=False)

    # Saving the converted audio in a mp3 file
    name = "Speech.mp3"

    myobj.save(os.path.join(cwd, name))
    os.system("mpg321 " + os.path.join(cwd, name))


def main():
    # Get the object to search
    while(to_search["valid"] == False):
        speak("Tell the object to search")
        get_the_search_word()
        if(to_search["valid"]):
            speak("Object to search is")
            speak(to_search["word"])
        else:
            speak("Some error occurred")


    if(not(os.path.exists(path))):
        os.mkdir(path)

    generate_frames()

    speak("Your surrounding")
    print(thread_data)
    x = len(thread_data)
    caption_sorted = OrderedDict(sorted(thread_data.items()))
    speak("from your left")
    y = 0
    for t in caption_sorted:
        # open the image
        fn = "frame_" + chr(int(t[6:]) + 65 - 1) + ".png"
        im = cv2.imread(os.path.join(path, fn))
        cv2.imshow(fn, im)
        cv2.waitKey(1000)
        speak(caption_sorted[t])
        y += 1
        if(y < x):
            speak("followed by")
        cv2.destroyAllWindows()
    speak("End of description")
    shutil.rmtree(path)
    os.remove(os.path.join(cwd, "Speech.mp3"))

def process_image(threadName, frame_file):
    print("Thread name : ", threadName)
    print("frame_file : ", frame_file)

    with open(os.path.join(path, frame_file), "rb") as f:
        data = f.read()
    data8uint = np.fromstring( data, np.uint8 ) # Convert string to an unsigned int array
    img = cv2.cvtColor( cv2.imdecode( data8uint, cv2.IMREAD_COLOR ), cv2.COLOR_BGR2RGB )
    json = None

    result = processRequest( json, data, headers, params )

    for obj in result['tags']:
        o = obj['name']
        objects.append(o)

    list_of_captions = result['description']['captions']
    list_of_captions.sort(key = lambda x: x["confidence"], reverse = True)

    thread_data[threadName] = list_of_captions[0]["text"]
    print(threadName, "objects - ", objects)
    print(threadName, "caption - ", list_of_captions[0]["text"])

if __name__ == "__main__":
    speak("Hello")
    main()
