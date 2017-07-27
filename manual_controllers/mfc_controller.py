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
import binascii

### Logging Config ###
showtime = time.strftime("%Y_%m_%d-%H_%M_%S", time.gmtime())
print('calibration' + showtime + '.log')
logger = logging.getLogger(__name__)
handler = logging.FileHandler('calibration' + showtime + '.log')
handler2 = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s:\t%(message)s')
handler.setFormatter(formatter)
handler2.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(handler2)
logger.setLevel(logging.DEBUG)

from calcCRC import calcCRC


serial_list = ['/dev/tty.usbserial-A800dars', '/dev/tty.usbserial', '/dev/tty.usbserial-AE01I93I', '/dev/tty.usbmodem1411', '/dev/tty.usbserial']
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


class MFC_Controller_One():
	def __init__(self):
		self.ser = serial.Serial(serial_list[4], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=3)
		time.sleep(1)
		logger.info("Starting MFC Controller")
		logger.debug("Connected over serial at " + str(self.ser.name))
		self.turn_on()

	def is_healthy(self):
		if (self.cmd_controller("?Srnm") == 'Srnm1380145\x93\r'):
			return(True)
		else:
			return(False)

	def read_streaming_state(self):
		self.cmd_controller('?Strm')

	def set_streaming_state(self, mode):
		self.cmd_controller('!Strm' + mode)

	def read_flow(self):
		self.cmd_controller("?Flow")

	def read_gas(self):
		self.cmd_controller('?Gasi')

	def set_gas(self, gas_index):
		# gasIndex value is 1 through 10
		"""
		1 - Air 
		2 - Argon
		3 - CO2
		4 - CO
		5 - He
		6 - H
		7 - CH4
		8 - N
		9 - NO
		10 - O
		"""
		rsp = "Gasi" + str(gas_index) 
		rsp = rsp + calcCRC(rsp) + '\x0d'
		if (self.cmd_controller("!Gasi" + str(gas_index)) == rsp):
			return(True)
		else:
			return(False)

	def set_setpoint(self, setpoint):
		rsp = "Sinv" + ('%.3f' % setpoint)
		rsp = rsp + calcCRC(rsp) + '\x0d'
		if (self.cmd_controller("!Sinv" + ('%.3f' % setpoint)) == rsp):
			return(True)
		else:
			return(False)

	def cmd_controller(self, cmd):
		crc = calcCRC(cmd)
		cmd = cmd + (crc) + '\x0d'
		self.ser.write(cmd)
		ser_rsp = self.ser.read(200)
		logger.debug("Output from MFC Controller cmd with repr(): " + repr(ser_rsp))
		logger.debug("Output from MFC Controller cmd *without* repr(): " + ser_rsp)
		return(ser_rsp)

	def turn_on(self):
		self.set_streaming("Echo")
		pass

def check_health():
	mc = MFC_Controller_One()
	if (mc.is_healthy() == True):
		# calboard controller is healthy and can continue
		logger.debug("MFC Controller is healthy, moving forward.\n\n")
		return(True)
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "MFC is unhealthy, stopping calibration.\n\n"
		logger.error(err_msg)
		return(False)

def run_cmds():
	mc_1 = MFC_Controller_One()

	if mc_1.set_setpoint(10) == True:
		print('we done it!')

if check_health():
	run_cmds()


