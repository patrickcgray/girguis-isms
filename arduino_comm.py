from time import sleep
import serial

ser = serial.Serial('/dev/tty.usbmodem1411', 9600) # Establish the connection on a specific port
#art_input = "111222121212"
#initial_status =  ser.readline()
#print(repr(initial_status))
#if initial_status == '1\r\n':
#    print("We're healthy. 100%")
#else:
#    print("Arduino issues... amirite?")
print("Starting up.")

while True:
    user_input = raw_input()
    if user_input == "-1":
        break
    if user_input == '':
        pass
    else: 
        # do I need to make sure it doesn't overrun the buffer on the arduino side?
        ser.write(user_input)
    newest_line = ser.readline() # Read the newest output from the Arduino
    print(newest_line)
