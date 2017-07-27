'''
Created on Feb, 27 2017

@author: pgray

@description: small app to command the temperature bath
'''

import serial
from Tkinter import *
import ttk
import time

serial_list = ['/dev/tty.usbserial-A800dars', '/dev/ttyUSB1', '/dev/ttyUSB2']
serial_check_list = [None] * len(serial_list)

def check_serial():
	#naive attempt to write to a serial port incased in a try/except in case it isn't plugged in
	for index, serial_port in enumerate(serial_list):
		try:
			ser = serial.Serial(serial_port)	  	# open serial port
			serial_check_list[index] = ser.name 	# check which port was really used
			#ser.write(b'hello')     				# write a string
			ser.close()             				# close port
			print("got one")
		except Exception as e:
			#print("Couldn't access serial port - error is:\n\t" + str(e))
			#template = "\nAn exception of type {0} occured. Arguments:\n{1!r}\n"
			#message = template.format(type(e).__name__, e.args)
			#print(message)
			pass
	return serial_check_list

def command_bath():
	print("Beginning attempt to connect over serial.")

	available_ports = check_serial()

	if not any(available_ports):
		print("ERROR: Serial connection issue. Aborting test.")

	else:
       
		print("Testing connection to Bath.")

		# run through a couple commands for the bath
		# for RS-232: pin 2-TX, 3-RX, 5-GND

		ser = serial.Serial('/dev/tty.usbserial-A800dars', 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)

		print(ser.name)

		
		ser.write(b"R T1 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	


		ser.write(b"R SP \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	

		ser.write(b"W P5 40 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	

		ser.write(b"R PU \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	


		ser.write(b"R PS \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	

		ser.write(b"R C5 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	

		"""

		ser.write(b"W SP1 20 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)				

		ser.write(b"R SP1 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	

		ser.write(b"W SP2 20 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)				

		ser.write(b"R SP2 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	


		ser.write(b"W SP3 20 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)				

		ser.write(b"R SP3 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	


		ser.write(b"W SP4 20 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)				

		ser.write(b"R SP4 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	


		ser.write(b"W SP5 20 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)				

		ser.write(b"R SP5 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)	

		"""
		"""

		ser.write(b"R T3 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)

		ser.write(b"R HA 0 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)

		ser.write(b"W HA 0 150.0 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)

		ser.write(b"R HA 0 \r\n")
		serial_response = ser.read(100)       	
		print(serial_response)

		ser.write(b"R LA 0 \r\n")
		serial_response = ser.read(100)
 		print(serial_response)

 		ser.write(b"W LA 0 -50.0 \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LA 0 \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R HW 0 \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"W HW 0 99.0 \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R HW 0 \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LW 0 \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"W LW 0 6.0 \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LW 0 \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		"""

		"""

		ser.write(b"R PS \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		


		ser.write(b"R PU \r")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R P5 \r")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LEVEL 0 \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LEVEL 1 \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LEVEL  \r\r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LEVEL\r\r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LEVEL\r \r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LEVEL\r\n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LEVEL \r")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LEVEL\r \n")
		serial_response = ser.read(100)
		print(serial_response)

		ser.write(b"R LEVEL\r")
		serial_response = ser.read(100)
		print(serial_response)

		"""


		print("serial response done")
		

		print("exiting test")

		ser.close()    

#check_serial()

command_bath()

