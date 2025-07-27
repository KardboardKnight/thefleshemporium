import os
import time
from PIL import Image
import pygame
import shutil
import subprocess
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import RPi.GPIO as GPIO
import random, glob
import fcntl
import struct

import sys
sys.path.append('/home/your_user/.local/lib/python3.8/site-packages')
       


servo_pin = 12
button_pin = 23
STOP_DUTY = 7.4
GPIO.setmode(GPIO.BCM)

mp = '/media/MY_PHOTO'
default_img_path = "/home/ethan/Default_Images"
display_time = 8
supported_ext = ('.jpg', '.jpeg', 'png', 'gif')
destination_dir = "/home/ethan/Pictures/floppy"
seen_device = None

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']
subfolder_id = '1DvL3SEw102bZ8vtAOMAaeD-FvL_JRTPH'

GPIO.setup(servo_pin, GPIO.OUT)
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

pwm=GPIO.PWM(servo_pin, 50)
pwm.start(STOP_DUTY)

def rotate_servo(duty_cycle, duration):
    pwm.ChangeDutyCycle(duty_cycle)
    time.sleep(duration)

# Authenticate the user
def authenticate():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_img_files(path):
    return [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(supported_ext)]

def display_images_fullscreen(image_path):
    pygame.init()
    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            return
    
    img = Image.open(image_path)
    img = img.convert('RGB')
    img = img.resize(screen.get_size(), Image.ANTIALIAS)
    mode = img.mode
    size = img.size
    data = img.tobytes()

    surface = pygame.image.fromstring(data, size, mode)
    screen.blit(surface, (0,0))
    pygame.display.flip()

    time.sleep(display_time)
    pygame.quit()

# Upload images from local directory
def upload_images_from_folder(folder_path):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    for filename in os.listdir(folder_path):
        print(filename)
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
            file_metadata = {'name': filename, 'parents': [subfolder_id]}
            media = MediaFileUpload(os.path.join(folder_path, filename), resumable=True)
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"Uploaded {filename}, file ID: {file.get('id')}")

def delete_files(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

# def check_and_run_once_per_mount():
#     global seen_device
#     print("Checking for Floppy disk")
#     current_device = os.stat(mp).st_dev
#     print(f"previous device id {seen_device} current device id {current_device}")
#     if current_device != seen_device:
#         process_new_floppy()
#         seen_device = current_device
#     else:
#         print("Not a new floppy disk:")
#         result = subprocess.run(['umount', '/media/ethan/MY_PHOTO'])
#         print(str(result.returncode))
#         return

def process_new_floppy():
    # was_mounted = attempt_to_mount()
    # if was_mounted:
    images = get_img_files(mp)
    for image in images:
        shutil.copy2(image, destination_dir)
        display_images_fullscreen(image)
    
    upload_images_from_folder(destination_dir)
    delete_files(destination_dir)

def show_default_images():
    try:
        images = get_img_files(default_img_path)#glob.glob(random.choice(default_img_path))
        random_image = random.choice(images)
        display_images_fullscreen(random_image)
    except:
        print("Uh Oh, cannot find default images.")        

def is_disk_inserted():
    device_path = '/dev/sda'

    req = 0x80081272 # BLKGETSIZE64, result is bytes as unsigned 64-bit integer (uint64)
    buf = b' ' * 8
    fmt = 'L'
    try:
        with open(device_path) as dev:
            buf = fcntl.ioctl(dev.fileno(), req, buf)
        bytes = struct.unpack('L', buf)[0]

        # print(str(bytes))
        return True
    except:
        return False

def attempt_to_mount():
    try:
        result = subprocess.run(['pmount', '/dev/sda', 'MY_PHOTO'])
        print(str(result.returncode))
        if result.returncode == 0:
            return True
        else:
            return False
    except:
        pass

    return False

if __name__ == "__main__":
    os.makedirs(destination_dir, exist_ok=True)
    while(True):
        try:
            if(is_disk_inserted()):
                print('disk is inserted')
                was_mounted = attempt_to_mount()
                if was_mounted:
                #     print('run your main logic here')
                #check_and_run_once_per_mount()
                    print("Processing new floppy")
                    process_new_floppy()
                else:
                    print('is already mounted, not going to do anything')
                    result = subprocess.run(['pumount', '/media/MY_PHOTO'])
            else:
                print('no disk inserted')
                show_default_images()

            for i in range(8):
                if (GPIO.input(button_pin)) == False:
                    print("Dispensing card")
                    rotate_servo(STOP_DUTY+5.0, .8)
                    rotate_servo(STOP_DUTY, 5)
                time.sleep(1)


        except KeyboardInterrupt:
            pwm.stop()
            GPIO.cleanup()
