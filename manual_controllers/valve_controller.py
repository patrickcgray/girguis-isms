import serial

ser = serial.Serial("/dev/tty.usbserial181", 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
print("writing out")
ser.write(b"CP\r\n")
ser_rsp = ser.read(100)
print(repr(ser_rsp))
print(ser_rsp)
#current_position = int(filter(str.isdigit, ser_rsp))
#print(current_position)

if ("Bad command" in ser_rsp):
	print("it was a bad cmd")

print("done reading")
