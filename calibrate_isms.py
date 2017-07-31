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
from calcCRC import calcCRC

### Logging Configuration (using default python logging module)
logger = logging.getLogger(__name__)
showtime = time.strftime("%Y_%m_%d-%H_%M_%S", time.gmtime())
handler = logging.FileHandler('_calibration_' + showtime + '.log')
handler2 = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s:\t%(message)s')
handler.setFormatter(formatter)
handler2.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(handler2)
logger.setLevel(logging.DEBUG)

#logger for simple status information for data analysis
data_logger = logging.getLogger(__name__ + 'data')
data_handler = logging.FileHandler('data_calibration_' + showtime + '.log')
data_handler.setFormatter(formatter)
data_logger.addHandler(data_handler)
data_logger.setLevel(logging.INFO)

### Serial Device Controllers ###

# [bath controller, valve controller, hplc controller, calboard controller, mfc controller_one, mfc controller two]
serial_list = ['/dev/tty.usbserial-A800dars', '/dev/tty.usbserial186', '/dev/tty.usbmodem14131', '/dev/tty.usbmodem14111', '/dev/tty.usbserial']
# TODO need a version of this that works for Windows
serial_check_list = [None] * len(serial_list)

# abstract class that controller's inherit from. these are the object oriented code to command and
	# communicate with all serial devices
class Controller_Parent(object):
	def __init__(self):
		pass

	def is_healthy(self):
		pass

	def turn_on(self):
		pass

	def cmd_controller(self):
		pass

	def kill(self):
		pass

# temperature bath controller
# this controller is more thorougly commented to clarify the setup of the controllers, repeated code in 
	# following controllers is not commented
class Bath_Controller(Controller_Parent):
	def __init__(self, app):
		# establish serial control with serial device
		self.ser = serial.Serial(serial_list[0], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
		self.set_temp = None
		self.app = app
		logger.info("Starting Bath Controller.")
		logger.debug("Connected over serial at " + str(self.ser.name))
		
	def is_healthy(self):
		# this command stops the bath so only use upon startup, it is used because it give a consistent
			# reply to ensure communication has been established
		if (self.cmd_controller("W RR -1") == "$\r\n"):
			self.continuous_temp_update() # Bath is healthy so get it updating temp readout
			return(True)
		else:
			return(False)

	def continuous_temp_update(self):
		try:
			self.app.update_temp(self.read_temp())
		except:
			return
		self.app.after(5000, lambda: self.continuous_temp_update())

	# this tells the bath to turn on and will attempt to heat or cool to current setpoint
	def turn_on(self):
		if(self.cmd_controller("W GO 1") == "$\r\n"):
			logger.info("Bath Controller: Turned ON")
			return(True)
		else:
			return(False)

	# stops bath operation
	def stop_bath(self):
		self.cmd_controller("W RR -1")

	# this is the command logic which is used internally by this class and is specific to all controllers
	def cmd_controller(self, cmd):
		self.ser.write(b"" + cmd + "\r\n")
		ser_rsp = self.ser.read(100)
		logger.debug("Output from Bath Controller cmd: " + repr(ser_rsp))
		if (ser_rsp == "F001\r\n"):
			logger.error("Error from Bath Controller: " + repr(ser_rsp))
			# all cmd_controllers issue a "bad cmd" response for consistency
			return("bad cmd")
		# if the cmd was good then return whatever the device returned
		else:
			return(ser_rsp)

	def read_temp(self):
		ser_rsp = self.cmd_controller("R T1")
		if ser_rsp == "bad cmd":
			logger.warn("Not able to read temperature.")
			return(-999)
		else:
			return(float(ser_rsp.split(" ")[1]))

	def change_temp(self, temp):
		# todo do I need to check to make sure temp is within constraints set?
		ser_rsp = self.cmd_controller("W SP " + str(temp))
		if ser_rsp == "$\r\n":
			self.set_temp = temp
			logger.debug("Setting goal temp to: " + str(self.set_temp))
			self.app.update_goal_temp(self.set_temp)
			self.turn_on()
			return True
		else:
			return False

	def check_temp(self):
		current_temp = self.read_temp()
		# checking if temp is within .05 degrees of setpoint and if so reporting back True
		if (current_temp < self.set_temp + .05) and (current_temp > self.set_temp - .05):
			logger.info("Temperature reached. Carry on.")
			return(True)
		else:
			logger.info("Waiting for temperature to reach " + str(self.set_temp) + ".\t Current temp is: " + str(current_temp))
			return(False)

# controller for the Valco 6 Port Multiposition Valve Controller
class Valve_Controller(Controller_Parent):
	def __init__(self, app):
		self.ser = serial.Serial(serial_list[1], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
		logger.info("Starting Valve Controller")
		logger.debug("Connected over serial at " + str(self.ser.name))
		self.app = app

	def is_healthy(self):
		# asking for the part number and date of firmware to ensure device is communcating
		if (self.cmd_controller("VR") == "I-PD-AMHX88RD1\r01/03/2008\r"):
			return(True)
		else:
			return(False)

	def cmd_controller(self, cmd):
		self.ser.write(b"" + cmd + "\r\n")
		time.sleep(1)
		ser_rsp = self.ser.read(100)
		logger.debug("Output from Valve Controller cmd: " + repr(ser_rsp))
		if ("Bad command" in ser_rsp):
			logger.error("Error from Valve Controller: " + repr(ser_rsp))
			return("bad cmd")
		else:
			return(ser_rsp)

	def turn_on(self):
		# device is on upon power-up
		return(True)

	# set the valve position from 1 to 6
	def set_valve(self, valve_number):
		if (valve_number > 0 and valve_number < 7):
			current_position_response = self.cmd_controller("CP")
			current_position = int(filter(str.isdigit, current_position_response))
			if valve_number == current_position:
				return(True)
			else:
				ser_rsp = self.cmd_controller("GO " + str(valve_number))
				if ser_rsp != "bad cmd":
					logger.debug("Setting current valve to: " + str(valve_number))
					self.app.current_valve.set(valve_number)
					time.sleep(.5) # TODO need to calculate how long to wait for pump to match pressure
					return(True)
		return(False)

# controller for the HPLC pump
class Pump_Controller(Controller_Parent):
	#TODO need to look into fault clearing after overpressure
	def __init__(self):
		self.ser = serial.Serial(serial_list[2], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
		logger.info("Starting HPLC Pump Controller")
		logger.debug("Connected over serial at " + str(self.ser.name))

	def is_healthy(self):
		# asking for pump type and firmware revision
		if (self.cmd_controller("ID") == "OK, 195016 Version 2.0.9/"):
			return(True)
		else:
			return(False)

	def cmd_controller(self, cmd):
		self.ser.write(b"" + cmd)
		ser_rsp = self.ser.read(100)
		logger.debug("Output from Pump Controller cmd: " + repr(ser_rsp))
		if ser_rsp == "Er/":
			logger.error("Error from Pump Controller: " + repr(ser_rsp))
			return("bad cmd")
		else:
			return(ser_rsp)

	def turn_on(self):
		# set the pump to run state
		if(self.cmd_controller("RU") == "OK/"):
			return(True)
		else:
			return(False)

	def set_flow_rate(self, flow_rate):
		if (self.cmd_controller("FI" + str(flow_rate)) == "OK/"):
			return(True)
		else:
			return(False)

	def stop_pump(self):
		# sets the pump to stop state
		if(self.cmd_controller("ST") == "OK/"):
			return(True)
		else:
			return(False)       
	
	def set_pressure_limit(self, limit):
		if(self.cmd_controller("UP" + str(limit)) == "OK/"):
			return(True)
		else:
			return(False)

	def clear_faults(self):
		if(self.cmd_controller("CF") == "OK/"):
			return(True)
		else:
			return(False)       

# controller for the arduino that controls the circuit board that controls the calibration board
class CalBoard_Controller(Controller_Parent):
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
	def state_one(self):
		# Normal operation while running the mass spec
		if self.cmd_controller("valves 1") == "valves 1\r\n":
			time.sleep(1)
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

	def state_four(self):
		# Releasing gas pressure from the system
		if self.cmd_controller("valves 4") == "valves 4\r\n":
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
		self.state_two()    # state two for filling the fluid reservoir
		time.sleep(1)       # allow time to change valves
		self.flush_on()     # begin filling fluid reservoir

	def stop_refill(self):
		self.flush_off()    # turn off pump
		time.sleep(2)       # allow time for pressure to die down from flush pump
		self.state_one()    # change back to standard ISMS calibration operation state
		time.sleep(1)       # allow time to change valves

	def read_press(self):
		#Command to get the pressure values
		# three values of the form "num, num, num" returned as a list of ints
		pressures = self.cmd_controller("press")
		return map(int, pressures.split(", "))


class MFC_Controller_Parent(Controller_Parent):
	def __init__(self):
		self.serial_num = None
		self.ser = None

	def is_healthy(self):
		if (self.cmd_controller("?Srnm") == self.serial_num):
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
		#self.set_streaming_state("Echo")
		pass

	def turn_off(self):
		self.ser.close()

# mass flow controller one
# this is typically the Nitrogen MFC
class MFC_Controller_One(MFC_Controller_Parent):
	def __init__(self, app):
		# The serial_list index and serial number will change depending on device
		self.ser = serial.Serial(serial_list[4], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=3)
		time.sleep(1)
		logger.info("Starting MFC Controller One (Nitrogen)")
		logger.debug("Connected over serial at " + str(self.ser.name))
		self.serial_num = 'Srnm210704\x8c\x92\r'
		self.turn_on()

# mass flow controller two
# this is typically the calibration gas MFC
class MFC_Controller_Two(MFC_Controller_Parent):
	def __init__(self, app):
		self.ser = serial.Serial(serial_list[4], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=3)
		time.sleep(1)
		logger.info("Starting MFC Controller Two (Calibration Gas)")
		logger.debug("Connected over serial at " + str(self.ser.name))
		self.serial_num = 'Srnm210704\x8c\x92\r'
		self.turn_on()

		# Will need to look at app.current_gas in order to appropriately set the gas index on the MFC

# not currently in use, just a skeleton controller for commanding the future sampling setup
class Sampling_Controller(Controller_Parent):
	def __init__(self):
		#self.ser = serial.Serial(serial_list[3], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
		logger.info("Starting Sampling Controller")
		#print("Connected over serial at " + str(self.ser.name))

	def is_healthy(self):
		if (True):
			return(True)
		else:
			return(False)

	def cmd_controller(self, cmd):
		pass

	def turn_on(self):
		pass
	
	def check_sampling(self, app):
		if (app.currently_sampling):
			return(False)
		else:
			return(True)


### Main Tkinter Application ###

# this is the actual GUI code that is executed in the main() function to create the GUI
class Application(tk.Frame):
	def __init__(self, master=None):
		tk.Frame.__init__(self, master, padx=25, pady=25)
		self.grid()
		logger.info("Firing up the GUI window.")
		self.master.title('Girguis ISMS Calibration')
		
		# creating all application variables
		self.status                 = tk.StringVar()
		self.status.set("Awaiting instruction.")
		self.details                = tk.StringVar()
		self.details.set("Please initiate a command.")
		self.errors                 = tk.StringVar()
		self.errors.set("No errors yet detected.")
		self.calibrating            = tk.BooleanVar()
		self.calibrating            = False
		self.paused                 = tk.BooleanVar()
		self.paused                 = False
		self.currently_sampling     = tk.BooleanVar()
		self.currently_sampling     = False
		self.refilling_fr           = tk.BooleanVar()
		self.refilling_fr           = False
		self.system_healthy         = tk.BooleanVar()
		self.system_healthy         = False
		self.system_setup     		= tk.BooleanVar()
		self.system_setup 	        = False
		self.safe_to_kill           = tk.BooleanVar()
		self.safe_to_kill           = False
		self.current_valve          = tk.IntVar()
		self.time_string            = tk.IntVar()
		self.temp_readout           = tk.DoubleVar()
		self.goal_temp              = tk.DoubleVar()
		self.set_valve              = tk.IntVar()
		self.set_temp               = tk.DoubleVar()
		self.in_manual              = False
		self.gas_index				= tk.IntVar()
		self.gas_index				= -1

		self.createWidgets()

	# this fcn defines and creates all the visual components of the GUI
	def createWidgets(self):

		device_readouts = tk.Frame(self, borderwidth=2, relief=tk.SUNKEN, pady=10, padx=10, bg="grey")
		device_readouts.grid(column=2, row=1, sticky=tk.NW)
		ttk.Label(device_readouts, text="Device Readouts").grid(column=1, row=1, columnspan=3)		
		ttk.Label(device_readouts, text="current valve").grid(column=2, row=2)
		ttk.Label(device_readouts, textvariable=self.current_valve).grid(column=1, row=2)
		ttk.Label(device_readouts, text="temp readout").grid(column=2, row=3)
		ttk.Label(device_readouts, textvariable=self.temp_readout).grid(column=1, row=3)
		ttk.Label(device_readouts, text="goal temp").grid(column=2, row=4)
		ttk.Label(device_readouts, textvariable=self.goal_temp).grid(column=1, row=4)
		ttk.Label(device_readouts, text="seconds elapsed").grid(column=2, row=5)
		ttk.Label(device_readouts, textvariable=self.time_string).grid(column=1, row=5)

		status_readouts = tk.Frame(self, borderwidth=2, relief=tk.SUNKEN, pady=10, padx=10, bg="grey")
		status_readouts.grid(column=2, row=2, sticky=tk.NW)
		ttk.Label(status_readouts, text="Status Readouts").grid(column=1, row=1, columnspan=2)
		ttk.Label(status_readouts, text="Status:").grid(column=1, row=2)
		ttk.Label(status_readouts, textvariable=self.status).grid(column=2, row=2, columnspan=2)
		ttk.Label(status_readouts, text="Details:").grid(column=1, row=3)
		ttk.Label(status_readouts, textvariable=self.details).grid(column=2, row=3, columnspan=2)
		ttk.Label(status_readouts, text="Errors:").grid(column=1, row=4)
		ttk.Label(status_readouts, textvariable=self.errors).grid(column=1, row=4, columnspan=2)

		control_frame = tk.Frame(self, borderwidth=2, relief=tk.RAISED, pady=10, padx=10, bg="grey")
		control_frame.grid(column=1, row=1, rowspan=2, sticky=tk.NW)
		ttk.Button(control_frame, text="Run Pre-Check", command=self.check_health).grid(column=1, row=1)
		ttk.Button(control_frame, text="Setup Calibration", command=self.create_setup_window).grid(column=1, row=2)
		ttk.Label(control_frame, text="").grid(column=1, row=3)
		ttk.Button(control_frame, text="Begin Calibration", command=self.calibrate).grid(column=1, row=4)
		ttk.Button(control_frame, text="Pause Calibration", command=self.pause).grid(column=1, row=5)
		ttk.Button(control_frame, text="Un-pause Calibration", command=self.unpause).grid(column=1, row=6)
		ttk.Label(control_frame, text="").grid(column=1, row=7)
		ttk.Button(control_frame, text="Sampling Complete", command=self.sample_complete).grid(column=1, row=8)
		ttk.Button(control_frame, text='Start FR Refill', command= lambda: self.start_refill()).grid(column=1, row=9)
		ttk.Button(control_frame, text='Stop Refilling', command= lambda: self.stop_refill()).grid(column=1, row=10)
		ttk.Label(control_frame, text="").grid(column=1, row=11) 
		ttk.Button(control_frame, text="Open Manual Controls", command=self.create_manual_window).grid(column=1, row=12)

		quit_frame = tk.Frame(self, borderwidth=2, relief=tk.GROOVE, pady=10, padx=10, bg="grey")
		quit_frame.grid(column=2, row=3, sticky=tk.SE)
		ttk.Button(quit_frame, text='Quit', command= lambda: self.kill()).grid(column=1, row=1)
		
		# create padding for all items
		for child in self.winfo_children():
			child.grid_configure(padx=5, pady=5)
		for child in control_frame.winfo_children():
			child.grid_configure(padx=5, pady=5, sticky=tk.W)
		for child in device_readouts.winfo_children():
			child.grid_configure(padx=5, pady=5, sticky=tk.W)
		for child in status_readouts.winfo_children():
			child.grid_configure(padx=5, pady=5, sticky=tk.W)

	def kill(self):
		logger.info("Running through kill application safety procedures.\n\n")
		self.quit()
		if self.safe_to_kill:
			self.quit()
		else:
			#TODO do I need to kill anything else here to be safe?
			#TODO make sure I set up multiple try blocks here otherwise it will bail after any one error
			try:
				bc = Bath_Controller(self)
				bc.stop_bath()
				bc.ser.close()
				# also need to kill the pump
				pc = Pump_Controller()
				pc.stop_pump()
				pc.ser.close()

				vc = Valve_Controller(self)
				vc.set_valve(1)
				vc.ser.close()

				cc = CalBoard_Controller()
				cc.state_four()
				cc.ser.close()

				self.safe_to_kill = True
				self.quit()
			except Exception as e:
				template = str(type(e).__name__) + " occured. Arguments:" + str(e.args)
				logger.error(template)
				logger.warn("Not able to kill one or more serial devices.")
				self.quit()

			
	def create_manual_window(self):
		if not self.system_healthy:
			err_msg = "System has not passed health check!"
			self.errors.set(err_msg)
			logger.warn(err_msg)
		elif not self.paused and self.calibrating:
			err_msg = "System is in calibration mode and has not been paused!"
			self.errors.set(err_msg)
			logger.warn(err_msg)
		else:
			self.status.set("Manual mode engaged.")
			logger.info("Manual mode engaged.")
			self.in_manual = True

			t = tk.Toplevel(self, padx=50, pady=50)
			t.title("Manual Controls")

			ttk.Entry(t, width=7, textvariable=self.set_valve).grid(column=1, row=1)
			ttk.Button(t, text="Set Valve", command=self.manual_set_valve).grid(column=2, row=1)

			ttk.Entry(t, width=7, textvariable=self.set_temp).grid(column=1, row=2)
			ttk.Button(t, text="Set Temp", command=self.manual_set_temp).grid(column=2, row=2)
			
			ttk.Button(t, text='Done', command= lambda : self.disengage_manual(t)).grid(column=2, row=3)

			# create padding for all items
			for child in t.winfo_children():
				child.grid_configure(padx=5, pady=5, sticky=tk.W)


	def disengage_manual(self, manual_window):
		self.status.set("Manual mode disengaged.")
		logger.info("Manual mode disengaged.")
		self.in_manual = False
		manual_window.destroy()

	def create_setup_window(self):
		if not self.system_healthy:
			err_msg = "System has not passed health check!"
			self.errors.set(err_msg)
			logger.warn(err_msg)
		else:
			logger.info("Setting up calibration parameters.")
			t = tk.Toplevel(self, padx=50, pady=50)
			t.title("Calibration Setup")

			ttk.Label(t, text="Choose a gas").grid(column = 2, row = 2)

			gas_options = ["Carbon Dioxide","Hydrogen","Oxygen","Methane", "Nitrogen", "Sulfide"]
			self.current_gas = tk.StringVar()
			ttk.OptionMenu(t, self.current_gas, gas_options[0], *gas_options, command=self.gas_selected).grid(column=2,row=3)
			
			ttk.Button(t, text='Done', command=lambda : self.calibration_setup(t)).grid(column=2, row=5)

			# create padding for all items
			for child in t.winfo_children():
				child.grid_configure(padx=5, pady=5, sticky=tk.W)

	def check_health(self):
		if (system_health_check(self)):
			self.system_healthy = True
		else:
			self.system_healthy = False

	def calibration_setup(self, setup_window):
		# turning on the MFCs
		mfc1 = MFC_Controller_One(self)
		#mfc2 = MFC_Controller_Two(self)
		#TODO need to check what the setpoints here should be
		mfc1.set_setpoint(200)
		#mfc2.set_setpoint(10)

		#mfc1.set_gas(8) 					#setting gas to Nitrogen
		mfc1.set_gas(self.gas_selected) 	#setting gas to gas_selected

		mfc1.ser.close()
		#mfc2.ser.close()

		data_logger.info("MFCs On.")
		self.status.set("Calibration setup complete.")
		logger.info("Calibration setup complete.")
		data_logger.info("Calibration setup complete.")
		self.system_setup = True
		setup_window.destroy()

	def update_temp(self, current_temp):
		self.temp_readout.set(current_temp)

	def update_goal_temp(self, the_set_temp):
		 self.goal_temp.set(the_set_temp)

	def begin_timer(self, start_time):
		self.time_string.set(math.floor(time.time() - start_time))
		self.after(5000, lambda: self.begin_timer(start_time))

	def sample_complete(self):
		self.currently_sampling = False

	def start_refill(self):
		self.refilling_fr = True
		cc = CalBoard_Controller()
		cc.refill_fr()

	def stop_refill(self):
		cc = CalBoard_Controller()
		cc.stop_refill()
		self.refilling_fr = False

	def calibrate(self):
		if not self.system_healthy:
			err_msg = "System has not passed health check!"
			self.errors.set(err_msg)
			logger.warn(err_msg)
		if not self.system_setup:
			err_msg = "You have not setup the system yet. Click 'Setup Calibration'."
			self.errors.set(err_msg)
			logger.warn(err_msg)
		else:
			calibrate_master(self)

	def pause(self):
		if self.calibrating:
			self.status.set("Calibration paused.")
			logger.info("Calibration paused.")
			self.paused = True

	def unpause(self):
		if self.in_manual:
			self.status.set("Please disengage manual mode.")
			logger.warn("Please disengage manual mode.")
		if self.calibrating and self.paused:
			self.status.set("Calibration resumed.")
			logger.info("Calibration resumed.")
			self.paused = False

	def manual_set_temp(self):
		if not self.in_manual:
			# report some error and don't proceed
			err_msg = "Not safely in manual mode."
			self.errors.set(err_msg)
			logger.warn(err_msg)
			return
		bc = Bath_Controller(self)
		input_temp = self.set_temp.get()
		bc.change_temp(input_temp)
		bc.turn_on()
		self.details.set("Commanding temp to " + str(input_temp))
		logger.info("Commanding temp to " + str(input_temp))
		# todo need to fix this!!
		bc.check_temp()
		bc.ser.close()

	def manual_set_valve(self):
		if self.in_manual:
			vc = Valve_Controller(self)
			commanding = vc.set_valve(self.set_valve.get())
			vc.ser.close()
			if (commanding == True):
				self.details.set("Commanding valve: " + str(self.set_valve.get()))
				logger.info("Commanding valve to: " + str(self.set_valve.get()))
			else:
				err_msg = "Could not command to designated valve."
				self.errors.set(err_msg)
				logger.error(err_msg)
		else:
				err_msg = "We're not in manual mode!"
				self.errors.set(err_msg)
				logger.warn(err_msg)

	# triggered on change in gas drop down
	# TODO there is no default Sulfide in the MFC
	def gas_selected(self, value):
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
		if value == "Carbon Dioxide":
			self.gas_index = 3
		elif value == "Hydrogen":
			self.gas_index = 6
		elif value == "Oxygen":
			self.gas_index = 10
		elif value == "Methane":
			self.gas_index = 7
		elif value == "Nitrogen":
			self.gas_index = 8
		elif value == "Sulfide":
			self.gas_index = 1
		else:
			self.gas_index = 1

### Utility Functions

def check_serial():
	for index, serial_port in enumerate(serial_list):
		try:
			ser = serial.Serial(serial_port, timeout=2)        # open serial port
			serial_check_list[index] = ser.name     		# check which port was really used
			ser.close()                             	# close port
			logger.debug("Acquired serial connection.")
		except Exception as e:
			template = str(type(e).__name__) + " occured. Arguments:" + str(e.args)
			logger.error(template)
	return serial_check_list

def system_health_check(app):
	app.details.set("Running through prechecks...")
	logger.info("Running through prechecks...")

	# check that everything is attached to serial ports

	# TODO change this to check for all serial connections and need to decide how I handle errors
	if not any(check_serial()):
		app.errors.set("ERROR: Serial connection issue.")
		return(False)

	### Test Health of Controllers
	
	bc = Bath_Controller(app)
	if (bc.is_healthy() == True):
		# bath controller is healthy and can continue
		logger.debug("Bath Controller is healthy, moving forward.\n\n")
		bc.ser.close()
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "Bath Controller is unhealthy, stopping calibration.\n\n"
		app.errors.set(err_msg)
		logger.error(err_msg)
		return(False)

	vc = Valve_Controller(app)
	if (vc.is_healthy() == True):
		# valve controller is healthy and can continue
		logger.debug("Valve Controller is healthy, moving forward.\n\n")
		vc.ser.close()
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "Valve Controller is unhealthy, stopping calibration.\n\n"
		app.errors.set(err_msg)
		logger.error(err_msg)
		return(False)

	pc = Pump_Controller()
	if (pc.is_healthy() == True):
		# pump controller is healthy and can continue
		logger.debug("HPLC Pump Controller is healthy, moving forward.\n\n")
		pc.ser.close()
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "HPLC Pump is unhealthy, stopping calibration.\n\n"
		app.errors.set(err_msg)
		logger.error(err_msg)
		return(False)

	cc = CalBoard_Controller()
	if (cc.is_healthy() == True):
		# calboard controller is healthy and can continue
		logger.debug("Calboard Controller is healthy, moving forward.\n\n")
		cc.ser.close()
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "Calboard is unhealthy, stopping calibration.\n\n"
		app.errors.set(err_msg)
		logger.error(err_msg)
		return(False)

	# MFCs controllers
	mfc1 = MFC_Controller_One(app)
	if (mfc1.is_healthy() == True):
		# MFC controller is healthy and can continue
		logger.debug("MFC Controller One is healthy, moving forward.\n\n")
		mfc1.ser.close()
		#mfc1.turn_off()
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "MFC One is unhealthy, stopping calibration.\n\n"
		logger.error(err_msg)
		#mfc1.turn_off()
		return(False)
	"""
	mfc2 = MFC_Controller_Two(app)
	if (mfc2.is_healthy() == True):
		# MFC controller is healthy and can continue
		mfc2.turn_off()
		logger.debug("MFC Controller Two is healthy, moving forward.\n\n")
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "MFC Two is unhealthy, stopping calibration.\n\n"
		logger.error(err_msg)
		mfc2.turn_off()
		return(False)

	"""

	# RGA controller

	# turbo pump controller

	# GC controller

	app.details.set("Precheck complete! System healthy.")
	logger.debug("Precheck complete! System healthy.")
	return(True)

### END Utility Functions

# this is the main calibration function that is called and sets the system into its startup state
def calibrate_master(app):
	app.status.set("Calibration initiated.")
	logger.info("Calibration initiated.")
	data_logger.info("Calibration initiated.")
	app.calibrating = True
	app.begin_timer(time.time())
	# start things up in here

	bc = Bath_Controller(app)
	vc = Valve_Controller(app)
	pc = Pump_Controller()
	cc = CalBoard_Controller()
	#sc = Sampling_Controller()

	time.sleep(2) # allow controller startup time


	### Startup Procedure

	"""

	data collection is turned on for the mass spec

	run through prechecks (manually call check_health by running prechecks)

	manually check FR level and click to refill if needed

	get the loops up to their operational pressure
		HPLC turns on now
		MFCs turn on now

	"""

	cc.state_one() 				# put the calibration board into normal calibration operation state

	
	vc.set_valve(1) 			# setting the valve to the zero pressure setting
	#vc.ser.close()
	time.sleep(1)


	# turning on the HPLC pump
	pc.set_pressure_limit(6000) # 6000 psi
	time.sleep(1)
	pc.set_flow_rate(2000)		# 20ml/min
	time.sleep(1)
	pc.turn_on()				# setting to run state
	data_logger.info("HPLC Pump On.")

	#TODO I need to setup something that allows the pressure to equalize in the FR right here
		# or do it in the Setup Calibration section

	# operational values for queues
	#valve_queue    = deque([1, 6, 5, 4, 3, 2])
	#temp_queue         = deque([6, 4, 2])

	# testing values for queues
	valve_queue     = deque([5, 4])
	temp_queue      = deque([20.1, 20.2])

	# Boolean flags to inform calibrate_slave() about its proper state
	ready_for_pres_change   = True  # this starts True, and is reset True after last temp and sampling
	ready_for_temp_change   = False # this is set after pres change and after sampling
	waiting_for_temp        = False # this is set true when waiting for temp
	waiting_for_sample      = False # this is set true after temp reached and before sampling is done
	app.currently_sampling  = False # this is a temp solution until the real Sampling Controller is designed
	app.refilling_fr        = False # flag that is changed to True when FR refill button is pushed 
	app.paused				= True 	# the station starts paused so that the user can wait for it to pressurize  

	data_logger.info("Calibration algorithm beginning.")
	calibrate_slave(app, bc, vc, pc, cc, valve_queue, temp_queue, ready_for_pres_change, ready_for_temp_change, waiting_for_temp, waiting_for_sample)

# calibration slave function that is repeatedly called after 5 seconds everytime it complete
	# this delay allows the GUI to remain functional
def calibrate_slave(app, bc, vc, pc, cc, valve_queue, temp_queue, ready_for_pres_change, ready_for_temp_change, waiting_for_temp, waiting_for_sample):
	# test this entirely

	if app.paused:
		logger.debug("Calibration paused.")
		app.details.set("Calibration paused.")
	else:
		app.details.set("Calibration ongoing.")
		logger.debug("Calibration ongoing.")
		if ready_for_pres_change:
			logger.debug("Ready for pressure change.")
			valve_port = valve_queue.popleft()
			vc.set_valve(valve_port)
			data_logger.info("Pressure set to BPV " + str(valve_port))
			#TODO need to fix pressure transducers or just use pump press reading
			logger.info("Pressure is: " + str(cc.read_press()))
			ready_for_pres_change = False
			ready_for_temp_change = True
		if ready_for_temp_change:
			logger.debug("Ready for temp change.")
			temp_setting = temp_queue.popleft()
			bc.change_temp(temp_setting)
			data_logger.info("Temp set to " + str(temp_setting))
			ready_for_temp_change = False
			waiting_for_temp = True
		if waiting_for_temp:
			logger.debug("Waiting for temp equilibration.")
			if(bc.check_temp()): # returns True if bath is at set_temp is met
				logger.debug("Temperature reached.")
				data_logger.info("Temp reached setpoint.")
				waiting_for_temp = False
				waiting_for_sample = True
				app.currently_sampling = True
		if waiting_for_sample:
			logger.debug("Waiting for sample.")
			app.details.set("Waiting for sample.")
			if app.refilling_fr:
				logger.info("Refilling FR.")
				app.details.set("Refilling FR.")
			if not app.currently_sampling:
				logger.info("Done sampling.")
				app.details.set("Done sampling.")
				data_logger.info("Sample taken.")
				waiting_for_sample = False 
			if not waiting_for_sample:
				logger.debug("Checking remaining temp and valve queues.")
				if temp_queue: # if there are temps left in the temp queue keep running through at same pres
					logger.debug("Temp queue still exists.")
					ready_for_temp_change = True
				elif valve_queue: # if there are pressures left refill temp queue and move on to next pres
					logger.debug("Valve queue still exists.")
					temp_queue = deque([20.1, 20.2])
					ready_for_pres_change = True
				else: # if there are not temps and no pressures left the calibration is complete
					app.status.set("Calibration complete!")
					data_logger.info("Calibration complete.")
					logger.info("Calibration complete!")
					logger.info("Approx calibration time was: " + str(app.time_string.get()))
					app.calibrating = False
					return 

	# check state every 5 seconds and take necessary next action if not waiting
	app.after(5000, lambda: calibrate_slave(app, bc, vc, pc, cc, valve_queue, temp_queue, ready_for_pres_change, ready_for_temp_change, waiting_for_temp, waiting_for_sample))


def main():
	app = Application()         
	app.mainloop()    

if __name__ == '__main__':
	main()
