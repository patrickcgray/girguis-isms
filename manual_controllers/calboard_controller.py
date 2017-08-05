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
#handler = logging.FileHandler('calibration.log')
handler2 = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s:\t%(message)s')
#handler.setFormatter(formatter)
handler2.setFormatter(formatter)
#ogger.addHandler(handler)
logger.addHandler(handler2)
logger.setLevel(logging.DEBUG)


#serial_list = ['/dev/tty.usbserial-A800dars', '/dev/tty.usbserial', '/dev/tty.usbserial-AE01I93I', '/dev/tty.usbmodem14111']
serial_list = ['', '', '', 'COM28', '']
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


# controller for the arduino that controls the circuit board that controls the calibration board
class CalBoard_Controller():
	def __init__(self):
		self.ser = serial.Serial(serial_list[3], 9600, timeout=3)
		time.sleep(1)
		logger.info("Starting Calibration Board Controller")
		logger.debug("Connected over serial at " + str(self.ser.name))

	def is_healthy(self):
		if (self.cmd_controller("?") == '1\r\n'):
			return(True)
		else:
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

	# these commands change the state of the solenoid valves on the calibration board
	def normal_operation(self, gas_outlet="v9"):
		# Normal operation while running the mass spec with gas outlet v9
		if self.cmd_controller("normal_operation_" + gas_outlet) == "normal_operation_" + gas_outlet + "\r\n":
			time.sleep(1)
			return True
		return False

	def seawater_in(self):
		# Filling an empty fluid reservoir with seawater
		if self.cmd_controller("seawater_in") == "seawater_in\r\n":
			return True
		return False

	def di_water_in(self):
		# Filling an empty fluid reservoir with seawater
		if self.cmd_controller("di_water_in") == "di_water_in\r\n":
			return True
		return False

	def emptying_fr(self):
		# Emptying the fluid reservoir
		# Fluid is pushed out of reservoir by gas
		if self.cmd_controller("emptying_fr") == "emptying_fr\r\n":
			return True
		return False

	def release_press(self):
		# Releasing gas pressure from the system
		if self.cmd_controller("release_press") == "release_press\r\n":
			return True
		return False

	# these two commands turn on and off the flush pump on the calibration board
	def flush_on(self):
		# Ensure that we're in state 2 before doing this
		if (self.cmd_controller("flushOn") == "flushOn"):
			return True
		return False

	def flush_off(self):
		if (self.cmd_controller("flushOff") == "flushOff"):
			return True
		return False

	def refill_fr(self):
		self.seawater_in()  # state two for filling the fluid reservoir
		time.sleep(1)       # allow time to change valves
		self.flush_on()     # begin filling fluid reservoir

	def stop_refill(self, gas_outlet="v9"):
		self.flush_off()    				# turn off pump
		time.sleep(2)       				# allow time for pressure to die down from flush pump
		self.normal_operation(gas_outlet)   # change back to standard ISMS calibration operation state
		time.sleep(1)      					# allow time to change valves

	def read_press(self):
		#Command to get the pressure transducer values
		# three values of the form "high_press, low_press, high_low_press" returned as a list of ints
		pressures 		= self.cmd_controller("press")
		press_list 		= map(int, pressures.split(", "))
		high_press 		= 2000.0 * (press_list[0]/1023.0) * 5.0 - 1000.0
		low_press 		= 75.0   * (press_list[1]/1023.0) * 5.0 - 37.5
		high_low_press 	= 750.0 * (press_list[2]/1023.0) * 5.0 - 375.0
		#pressure 	= max pressure/(4.5V-.5V) * (voltage/max voltage) * 5V - offset (max pressure/(4.5V-.5V)*.5V)

		converted_pressures = [high_press, low_press, high_low_press]
		final_pressures = []
		print(converted_pressures)
		for pressure in converted_pressures:
			if pressure < 0.00:
				pressure = 0.00
			pressure = float("{0:.2f}".format(pressure))
			final_pressures.append(pressure)

		return(final_pressures)


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
				cc.normal_operation("v9")
			elif user_input == 2:
				cc.normal_operation("v8")
			elif user_input == 3:
				cc.seawater_in()
			elif user_input == 4:
				cc.di_water_in()
			elif user_input == 5:
				cc.release_press()
			elif user_input == 6:
				cc.flush_off()
			elif user_input == 7:
				print(cc.read_press())
			elif user_input == -1:
				cc.ser.close()
				break
			else:
				print("didn't match option")




