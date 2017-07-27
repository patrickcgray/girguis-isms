'''
Created on Mar, 03 2017

@author: pgray

@description: desktop calibration app for Girguis ISMS
'''

import Tkinter as tk
import ttk
import serial
import time
from collections import deque
import logging
import math

### Logging Config ###

logger = logging.getLogger(__name__)
handler = logging.FileHandler('calibration.log')
handler2 = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s:\t%(message)s')
handler.setFormatter(formatter)
handler2.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(handler2)
logger.setLevel(logging.DEBUG)


serial_list = ['/dev/tty.usbserial-A800dars', '/dev/tty.usbserial', '/dev/tty.usbserial-AE01I93I', '/dev/tty.usbmodem1411']
serial_check_list = [None] * len(serial_list)

def check_serial():
	print("************ checking serial")
	for index, serial_port in enumerate(serial_list):
		try:
			ser = serial.Serial(serial_port)	  	# open serial port
			serial_check_list[index] = ser.name 	# check which port was really used
			ser.close()             				# close port
			logger.debug("Acquired serial connection.")
		except Exception as e:
			template = str(type(e).__name__) + " occured. Arguments:" + str(e.args)
			logger.error(template)
	return serial_check_list


class CalBoard_Controller():
	def __init__(self):
		self.ser = serial.Serial(serial_list[3], 9600)
		time.sleep(1)
		logger.info("Starting Calibration Board Controller")
		logger.debug("Connected over serial at " + str(self.ser.name))

	def is_healthy(self):
		if (self.cmd_controller("?") == '1\r\n'):
			print("*********we're healthy")
			return(True)
		else:
			print("***********is healthy from calboard response begin***")
			print(self.cmd_controller("?"))
			print("****end msg****")
			return(False)

	def cmd_controller(self, cmd):
		self.ser.write(b"" + cmd)
		ser_rsp = self.ser.readline()
		logger.debug("Output from Calibration Board Controller cmd: " + repr(ser_rsp))
		if ser_rsp == "F001\r\n":
			logger.error("Error from Calibration Board Controller: " + repr(ser_rsp))
			return("bad cmd")
		else:
			return(ser_rsp)

	def turn_on(self):
		pass

	def state_one(self):
		# Normal operation while running the mass spec
		if self.cmd_controller("valves 1") == "valves 1\r\n":
			return True
		return False

	def state_two(self):
		# Filling an empty fluid reservoir
		if self.cmd_controller("valves 2") == "valves 2\r\n":
			return True
		return False

	def state_three(self):
		# Emptying the fluid reservoir
    	# Fluid is pushed out of reservoir by gas
		if self.cmd_controller("valves 3") == "valves 3\r\n":
			return True
		return False

	def flush_on(self):
		# Ensure that we're in state 2 before doing this
		if (self.cmd_controller("flushOn") == "flushOn"):
			return True
		return False

	def flush_off(self):
		if (self.cmd_controller("flushOff") == "flushOff"):
			return True
		return False

	def read_press(self):
		#Command to get the pressure values, three values of the form "num, num, num" returned as a list of ints
		pressures = self.cmd_controller("press")
		return map(int, pressures.split(", "))


def check_health():
	cc = CalBoard_Controller()
	if (cc.is_healthy() == True):
		# calboard controller is healthy and can continue
		logger.debug("Calboard Controller is healthy, moving forward.\n\n")
		return(True)
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "Calboard is unhealthy, stopping calibration.\n\n"
		logger.error(err_msg)
		return(False)

def run_valves():
	cc = CalBoard_Controller()
	#cc.is_healthy()
	
	#cc.state_one()
	#time.sleep(1)
	cc.state_two()
	time.sleep(1)
	cc.flush_on()
	#time.sleep(3)
	#cc.flush_off()
	
	

if any(check_serial()):
	print("**************passed check serial")
	print(serial_check_list)
	if check_health():
		print("passed health check")
		cc = CalBoard_Controller()
		while(True):
			user_input = input("Enter user input:")
			print(user_input)
			if user_input == 1:
				cc.state_one()
			elif user_input == 2:
				cc.state_two()
			elif user_input == 3:
				cc.state_three()
			elif user_input == 4:
				cc.flush_on()
			elif user_input == 5:
				cc.flush_off()
			elif user_input == -1:
				break
			else:
				print("didn't match option")




