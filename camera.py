import RPi.GPIO as GPIO #actually installed with pip3 install rpi.lgpio
import subprocess
import time
from datetime import datetime
import random
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import board
import neopixel

#Constants
#neopixels
pixel_count = 16    # Number of NeoPixels
led_order = neopixel.GRB  # NeoPixel color order
led_pin = board.D18       # GPIO18 (PWM output)
#camera
picture_taken_f = False
camera_shutter_pin = 26
timestamp = 0
#servos
X_PWM_PIN = 19 #GPIO18 pin 12
Y_PWM_PIN = 13 #GPIO13 pin 33
FREQ = 50
static_eye_position_f = 1
#datetime
current_datetime = 0

#Inits
GPIO.setmode(GPIO.BCM)
#initialize the NeoPixel strip
pixels = neopixel.NeoPixel(led_pin, pixel_count, brightness=0.25, auto_write=False, pixel_order=led_order)
#authenticate and create Google Drive client
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
#set up gpio for shutter press
GPIO.setup(camera_shutter_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#initialize the servos
GPIO.setup(X_PWM_PIN, GPIO.OUT)
GPIO.setup(Y_PWM_PIN, GPIO.OUT)
x_pwm = GPIO.PWM(X_PWM_PIN, FREQ)
y_pwm = GPIO.PWM(Y_PWM_PIN, FREQ)
x_pwm.start(7.5)
y_pwm.start(7.5)

#Functions
#set servo motor angle
def set_angle(pwm, angle):
    duty = (angle / 18.0) + 2.5  # Convert angle to duty cycle
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)
    pwm.ChangeDutyCycle(0)  # Stop sending signal to avoid jitter

#set neopixel color
def set_color(color):
    #set the deesired pixel colors
    pixels.fill(color)
    pixels.show()

#process button interrupt
def camera_shutter_callback(channel):
    print("taking picture\n")
    GPIO.remove_event_detect(camera_shutter_pin)

    handle_callback()  
   
    GPIO.add_event_detect(camera_shutter_pin, GPIO.FALLING, callback=camera_shutter_callback, bouncetime=2000)

#run the rpi camera subprocess to take a still
def take_picture():
    print("click\n")
    subprocess.run(["rpicam-still", "--ev", "+1.5", "--awb", "indoor", "-o", "printme.png", "--immediate"])

#exercise the effect lottery and possibly apply an effect
def effect_lottery(num):
    #print(num)
    match (num % 100):

        #add vignette
        case 1:
            print("Vignette\n")
            try:
                subprocess.run(["convert", "./printme.png", "-vignette", "20x0", "pme.png"]) # don't know if this is needed
            except:
                print("error")

        #add negative
        case 2:  
            print("Negative\n")
            subprocess.run(["convert", "printme.png", "-negate", "pme.png"])

        #add swirl
        case 3:
            print("Swirl\n")
            subprocess.run(["convert", "printme.png", "-swirl", "90", "pme.png"])

        #add mold effect
        case 4:
            print("Mold\n")
            subprocess.run(["convert", "-composite", "-gravity", "center", "-background", "transparent", "printme.png", "bg/mold.png", "printme.png"])  

        #add new mold frame
        case 5:
            print("Mold1\n")
            subprocess.run(["convert", "-composite", "-gravity", "center", "-background", "transparent", "printme.png", "bg/mold1.png", "printme.png"])

        #add smoke frame
        case 6:
            print("Smoke\n")
            subprocess.run(["convert", "-composite", "-gravity", "center", "-background", "transparent", "printme.png", "bg/smoke.png", "printme.png"]) 

        #add speckle frame
        case 7:
            print("Speckles\n")
            subprocess.run(["convert", "-composite", "-gravity", "center", "-background", "transparent", "printme.png", "bg/speckles.png", "printme.png"]) 

        #default, print the picture
        case _:
            print("Default\n")
            pass

#upload the photo to The Flesh Emporium Google Drive folder
def upload_photo():

    #rename photo
    global current_datetime 
    current_datetime = datetime.now()
    subprocess.run(["cp", "printme.png", f"{current_datetime}.png"])

    # Upload an image to The Flesh Emporium google drive folder
    file = drive.CreateFile({"parents": [{"id": "1DvL3SEw102bZ8vtAOMAaeD-FvL_JRTPH"}]})
    file.SetContentFile(f"{current_datetime}.png")
    try:
        file.Upload()
    except:
        print("Error uploading file")
    
    print("✅ Photo uploaded successfully!\n")

def handle_callback():
    global static_eye_position_f

    #change color and center eye
    print("Setting eye angle\n")
    static_eye_position_f = 0
    print("Setting eye color\n")
    set_color((255, 0, 0))

    #take picture
    take_picture()

    #fix rotation and make image monochrome
    subprocess.run(["convert", "-monochrome", "printme.png", "-rotate", "-90", "printme.png"])

    #generate random seed
    num = random.randrange(0, 1000, 1)
    
    #use effect lottery to affect the photo
    effect_lottery(num)
    
    #debug 
    # test=GPIO.input(gpio_pin)
    # print(f"this is the state of the gpio before resetting the event {test}")

    try:
        print("printing photo\n")
        subprocess.run(["lp", "printme.png"])
    except:
        print("Error")
    
    #upload the photo to the google drive
    upload_photo()

    # delete the file
    subprocess.run(["rm", "printme.png"])
    subprocess.run(["rm", f"{current_datetime}.png"])

    #reset eye movement and color
    static_eye_position_f = 1
    set_color((255, 255, 255))

def main():
    #set color  
    set_color((255,255,255)) #white
    time.sleep(1)

    try:
            #add the gpio interrupt event
        GPIO.add_event_detect(camera_shutter_pin, GPIO.FALLING, callback=camera_shutter_callback, bouncetime=2000)
        while True:
            if(static_eye_position_f):
                x_angle = random.choice([30, 60, 90, 120, 150])  # Select a random angle rounded to nearest 30 degrees
                y_angle = random.choice([30, 60, 90, 120])  # Select a random angle rounded to nearest 30 degrees
            else:
                x_angle = 120  # Set the eye to straight ahead while the picture is being taken
                y_angle = 30
            set_angle(x_pwm, x_angle)        
            set_angle(y_pwm, y_angle)
            print("x angle: ", f"{x_angle}", "y angle: ", f"{y_angle}")
            time.sleep(1)
            print("This is the camera shutter pin read: ", GPIO.input(camera_shutter_pin)) 
            time.sleep(1)

        # #debug
        # gpio_callback(gpio_pin)

    except RuntimeError as e:
        print(f"Error: {e}")

    except KeyboardInterrupt:
        print("Exiting program")

    except:
        print("Unhandled exception")

    finally:
        # lgpio.gpiochip_close(p)  # Clean up
        x_pwm.stop()
        y_pwm.stop()
        GPIO.cleanup()
        set_color((0, 0, 0))  # Turn off on exit

if __name__ == "__main__":
    main()