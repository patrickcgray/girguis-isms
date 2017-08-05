import serial
#serial_list = ["/dev/tty.usbmodem14131"]
serial_list = ['COM33']
ser = serial.Serial(serial_list[0], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
#ser.write(b"RU")
#ser.write(b"RE")
#ser.write(b"ST")
ser.write(b"ID")
#ser.write(b"FI2000")
ser_rsp = ser.read(100)
print(ser_rsp)
print(repr(ser_rsp))

if ser_rsp == "OK, 195016 Version 2.0.9/":
        print "we all good"

#ser.write(b"PI")
#ser_rsp = ser.read(100)
#print(ser_rsp)
