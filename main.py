from gpiozero import MotionSensor 
from gpiozero import Buzzer
from picamera import PiCamera
from datetime import datetime
import time
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
import email.encoders
import smtplib
import os
import email
from urllib.request import urlopen
import urllib.error
from subprocess import Popen,PIPE
import subprocess
import multiprocessing


pir = MotionSensor(4)
buzz= Buzzer(17)

camera = PiCamera()
camera.resolution = (640, 480)
#camera.resolution = (1024, 768)
camera.rotation = 180

h264Codec = ".h264"
mp4Codec = ".mp4"

motionCount=1
maxMotionCount=3
stopRecordingDelay=2

def isConnected():
    for timeout in [1,5,10,15]:
        try:
            response=urlopen('http://google.com',timeout=timeout)
            return True
        except urllib.error.URLError as err: pass
    return False

    

class SMS:
    def __init__(self,message,pNumber):
        self.message=message
        self.pNumber=pNumber
        
    def sendSMS(self):
        message=Popen(['echo',self.message],stdout=PIPE)
        SMS=Popen(['sudo','gammu','sendsms'
                  ,'TEXT',self.pNumber]
                  ,stdin=message.stdout,stdout=PIPE)
        message.stdout.close()
        output=SMS.communicate()[0]
#Variables   
emailAddress='YourEmailName@gmail.com' 
emailPassword="YourEmailPassword"

phoneNumber='YourPhoneNumber'
     
imageFolder='/home/pi/SharedPi/Images/'
videoFolder='/home/pi/SharedPi/Videos/'


  
print(' .....Monitoring System Started.....\n.....................................')
print('\nAn SMS message will be sent every '+str(maxMotionCount)+' detection(s) of motion ')

while True:

    # record h264 videoeo then save as mp4
    pir.wait_for_motion()
    print("\n"+str(motionCount)+" Motion(s) Detected")
   
    buzz.on()
    fileName = datetime.now().strftime("%m-%d-%Y @ %I-%M-%S %P")

    camera.start_recording(videoFolder+fileName + h264Codec)
    camera.capture(imageFolder+fileName+'.jpg')
    
    if motionCount==maxMotionCount:
        
        smsTime=datetime.now().strftime("%A %B %d %Y @ %I:%M:%S %P")
        msg='Motion was detected '+str(maxMotionCount)+' times on '+str(smsTime)+' please check: '+emailAddress+' for attachments'
        sms=SMS(msg,phoneNumber)  
        print('\nSending SMS !.....')
        multiprocessing.Process(target=sms.sendSMS, args=()).start() 
        motionCount=0
        
    pir.wait_for_no_motion()
    buzz.off()
    motionCount+=1
    
    time.sleep(stopRecordingDelay)
    camera.stop_recording()
    
    subprocess.run(['MP4Box', '-add','/home/pi/SharedPi/Videos/'+fileName + h264Codec,
                    '/home/pi/SharedPi/Videos/'+fileName + mp4Codec])
    subprocess.run(['rm','/home/pi/SharedPi/Videos/'+ fileName + h264Codec])
    
    print("\nVideo Processing Completed")
    
    video =videoFolder+fileName+mp4Codec
    image=imageFolder+fileName+'.jpg'
    attachments=[video,image]

    if isConnected():
        # Email Configuration
        FormatTime = datetime.now().strftime("%A %B %d %Y @ %I:%M:%S %P")
        message = MIMEMultipart()
        message["Subject"] = str('Motion Detected! on '+FormatTime)
        message["From"] = "CCTV Mointoring System"
        message["To"] = emailAddress
        Context = MIMEText("WARNING! Motion Detected!Check Attachments")
        message.attach(Context)

        for attachment in attachments:
        # attach taken image and videoeo to email
            payload = MIMEBase("application", "octet-stream")
            payload.set_payload(open(attachment, "rb").read())
            email.encoders.encode_base64(payload)
            payload.add_header("Content-Disposition", "attachment; filename= %s" % os.path.basename(attachment))
            message.attach(payload)


        # Setup gmail account and send email
            
        mailServer = smtplib.SMTP("smtp.gmail.com:587")
        mailServer.starttls()
        mailServer.login(emailAddress,emailPassword)
        print("\nSending Email !.....")
        mailServer.sendmail(emailAddress, emailAddress, message.as_string())
        mailServer.quit()
        print ("\nAn image & a video were succesfully sent to: "+emailAddress)
    else:
        print("\nFaild to connect to the internet, Sending sms instead.....")
        smsTime=datetime.now().strftime("%A %B %d %Y @ %I:%M:%S %P")
        warningMsg='\nMotion detected on '+str(smsTime)+', but no internet connection, images and videos are available offline\n'
        smsWarning=SMS(warningMsg,phoneNumber)
        multiprocessing.Process(target=smsWarning.sendSMS, args=()).start() 

    #    subprocess.run(["rm",video]) uncomment if you want to delete recorded footage after it was sent to email

