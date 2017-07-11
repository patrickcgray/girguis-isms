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

### Serial Device Controllers ###

# [bath, valve controller, hplc controller, ]
serial_list = ['/dev/tty.usbserial-A800dars', '/dev/tty.usbserial', '/dev/tty.usbserial-AE01I93I', '/dev/tty.usbmodem14131']
serial_check_list = [None] * len(serial_list)

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


class Bath_Controller(Controller_Parent):
	def __init__(self, app):
		self.ser = serial.Serial(serial_list[0], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
		self.set_temp = None
		self.app = app
		logger.info("Starting Bath Controller.")
		logger.debug("Connected over serial at " + str(self.ser.name))
		


	def is_healthy(self):
		# this command stops the controller so only use upon startup
		if (self.cmd_controller("W RR -1") == "$\r\n"):
			#self.continuous_update() # Bath is healthy to get it updating temp readout
			return(True)
		else:
			return(False)

	def continuous_update(self):
		self.app.update_temp(self.read_temp())
		self.app.after(5000, lambda: self.continuous_update())


	def turn_on(self):
		if(self.cmd_controller("W GO 1") == "$\r\n"):
			logger.info("Bath Controller: Turned ON")
			return(True)
		else:
			return(False)

	def kill(self):
		self.cmd_controller("W RR -1")

	def cmd_controller(self, cmd):
		self.ser.write(b"" + cmd + "\r\n")
		ser_rsp = self.ser.read(100)
		logger.debug("Output from Bath Controller cmd: " + repr(ser_rsp))
		if (ser_rsp == "F001\r\n"):
			logger.error("Error from Bath Controller: " + repr(ser_rsp))
			return("bad cmd")
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
		if (current_temp < self.set_temp + .05) and (current_temp > self.set_temp - .05):
			logger.info("Temperature reached. Carry on.")
			return(True)
		else:
			logger.info("Waiting for temperature to reach " + str(self.set_temp) + ".\t Current temp is: " + str(current_temp))
			return(False)

class Valve_Controller(Controller_Parent):
	def __init__(self, app):
		self.ser = serial.Serial(serial_list[1], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
		logger.info("Starting Valve Controller")
		logger.debug("Connected over serial at " + str(self.ser.name))
		self.app = app

	def is_healthy(self):
		if (self.cmd_controller("VR") == "I-PD-AMHX88RD1\r01/03/2008\r"):
			return(True)
		else:
			return(False)

	def cmd_controller(self, cmd):
		self.ser.write(b"" + cmd + "\r\n")
		ser_rsp = self.ser.read(100)
		logger.debug("Output from Valve Controller cmd: " + repr(ser_rsp))
		if ("Bad command" in ser_rsp):
			logger.error("Error from Valve Controller: " + repr(ser_rsp))
			return("bad cmd")
		else:
			return(ser_rsp)

	def turn_on(self):
		return(True)

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

#TODO need to look into fault clearing after overpressure
class Pump_Controller(Controller_Parent):
	def __init__(self):
		self.ser = serial.Serial(serial_list[2], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
		logger.info("Starting HPLC Pump Controller")
		logger.debug("Connected over serial at " + str(self.ser.name))

	def is_healthy(self):
		if (self.cmd_controller("ID") == "OK,v1.03 161794 firmware/"):
			return(True)
		else:
			return(False)

	def cmd_controller(self, cmd):
		self.ser.write(b"" + cmd)
		ser_rsp = self.ser.read(100)
		logger.debug("Output from Bath Controller cmd: " + repr(ser_rsp))
		if ser_rsp == "Er/":
			logger.error("Error from Pump Controller: " + repr(ser_rsp))
			return("bad cmd")
		else:
			return(ser_rsp)

	def turn_on(self):
		if(self.cmd_controller("RU") == "OK/"):
			return(True)
		else:
			return(False)
	
	def set_pressure_limit(self, limit):
		if(self.cmd_controller("UP" + str(limit)) == "OK/"):
			return(True)
		else:
			return(False)


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

	def refill_fr(self):
		self.state_two() 	# state two for filling the fluid reservoir
		time.sleep(1)		# allow time to change valves
		self.flush_on() 	# begin filling fluid reservoir

	def stop_refill(self):
		self.flush_off()	# turn off pump
		time.sleep(1)
		self.state_one()	# change back to standard ISMS calibration operation state
		time.sleep(1)		# allow time to change valves

	def read_press(self):
		#Command to get the pressure values, three values of the form "num, num, num" returned as a list of ints
		pressures = self.cmd_controller("press")
		return map(int, pressures.split(", "))


class Sampling_Controller(Controller_Parent):
	def __init__(self):
		#self.ser = serial.Serial(serial_list[3], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
		logger.info("Starting Sampling Controller")
		#print("Connected over serial at " + str(self.ser.name))

	def is_healthy(self):
		#if (self.cmd_controller("ID") == "OK,v1.03 161794 firmware/"):
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


### Main Tkinter Application

class Application(tk.Frame):
	def __init__(self, master=None):
		tk.Frame.__init__(self, master)
		self.grid()
		#self.configure(background='light grey')
		#s = ttk.Style()
		#s.configure('.', background='black', foreground='black')
		logger.info("Firing up the GUI window.")
		self.master.title('Girguis ISMS Calibration')
		
		# creating all application variables
		self.status 				= tk.StringVar()
		self.status.set("Awaiting instruction.")
		self.details 				= tk.StringVar()
		self.details.set("Please initiate a command.")
		self.errors 				= tk.StringVar()
		self.errors.set("No errors yet detected.")
		self.calibrating			= tk.BooleanVar()
		self.calibrating			= False
		self.paused 				= tk.BooleanVar()
		self.paused 				= False
		self.currently_sampling 	= tk.BooleanVar()
		self.currently_sampling 	= False
		self.refilling_fr 			= tk.BooleanVar()
		self.refilling_fr 			= False
		self.system_healthy 		= tk.BooleanVar()
		self.system_healthy 		= False
		self.safe_to_kill 			= tk.BooleanVar()
		self.safe_to_kill 			= False
		self.manual_state 			= tk.StringVar()
		self.manual_state.set("Manual Disengaged.")
		self.current_valve 			= tk.IntVar()
		self.time_string 			= tk.IntVar()
		self.temp_readout 			= tk.DoubleVar()
		self.goal_temp	 			= tk.DoubleVar()
		self.set_valve 				= tk.IntVar()
		self.set_temp 				= tk.DoubleVar()
		self.in_manual 				= False

		self.createWidgets()

	def createWidgets(self):
		#s = ttk.Style()
		#s.configure('.', background='black')

		ttk.Label(self, text="Manual Commands").grid(column=5, row=1)
		ttk.Label(self, textvariable=self.manual_state).grid(column=5, row=3, columnspan=1)

		ttk.Label(self, text="STATUS:").grid(column=2, row=8)
		ttk.Label(self, textvariable=self.status).grid(column=3, row=8, columnspan=2)

		ttk.Label(self, text="Details:").grid(column=2, row=9)
		ttk.Label(self, textvariable=self.details).grid(column=3, row=9, columnspan=2)

		ttk.Label(self, text="Errors:").grid(column=2, row=10)
		ttk.Label(self, textvariable=self.errors).grid(column=3, row=10, columnspan=2)

		ttk.Label(self, text="current valve").grid(column=3, row=2)
		ttk.Label(self, textvariable=self.current_valve).grid(column=2, row=2)

		ttk.Label(self, text="seconds elapsed").grid(column=3, row=5)
		ttk.Label(self, textvariable=self.time_string).grid(column=2, row=5)

		ttk.Label(self, text="temp readout").grid(column=3, row=3)
		ttk.Label(self, textvariable=self.temp_readout).grid(column=2, row=3)
		ttk.Label(self, text="goal temp").grid(column=3, row=4)
		ttk.Label(self, textvariable=self.goal_temp).grid(column=2, row=4)

		ttk.Button(self, text='Quit', command= lambda: self.kill()).grid(column=6, row=10)

		ttk.Button(self, text='Start FR Refill', command= lambda: self.start_refill()).grid(column=1, row=8)
		ttk.Button(self, text='Stop Refilling', command= lambda: self.stop_refill()).grid(column=1, row=9)

		ttk.Entry(self, width=7, textvariable=self.set_valve).grid(column=5, row=4)
		ttk.Button(self, text="Set Valve", command=self.manual_set_valve).grid(column=6, row=4)

		ttk.Entry(self, width=7, textvariable=self.set_temp).grid(column=5, row=5)
		ttk.Button(self, text="Set Temp", command=self.manual_set_temp).grid(column=6, row=5)

		ttk.Button(self, text="Run Pre-Check", command=self.check_health).grid(column=1, row=1)
		ttk.Label(self, text="---").grid(column=1, row=2)
		ttk.Button(self, text="Begin Calibration", command=self.calibrate).grid(column=1, row=3)
		ttk.Button(self, text="Pause Calibration", command=self.pause).grid(column=1, row=4)
		ttk.Button(self, text="Un-pause Calibration", command=self.unpause).grid(column=1, row=5)
		ttk.Label(self, text="---").grid(column=1, row=6)
		ttk.Button(self, text="Sampling Complete", command=self.sample_complete).grid(column=1, row=7)
		ttk.Button(self, text="Engage Manual", command=self.engage_manual).grid(column=5, row=2)
		ttk.Button(self, text="Disengage Manual", command=self.disengage_manual).grid(column=6, row=2)

		# create padding for all items
		for child in self.winfo_children(): 
			child.grid_configure(padx=5, pady=5)

	def kill(self):
		logger.info("Running through kill application safety procedures.\n\n")
		if self.safe_to_kill:
			self.quit()
		else:
			# todo do I need to kill anything else here to be safe?

			try:
				bc = Bath_Controller(self)
				bc.kill()
				# also need to kill the pump
				self.safe_to_kill = True
				self.quit()
			except Exception as e:
				template = str(type(e).__name__) + " occured. Arguments:" + str(e.args)
				logger.error(template)
				logger.warn("Not able to kill bath.")
				self.quit()
			

	def check_health(self):
		if (system_health_check(self)):
			self.system_healthy = True

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
		if self.system_healthy:
			calibrate_master(self)
		else:
			err_msg = "System has not passed health check!"
			self.errors.set(err_msg)
			logger.warn(err_msg)

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

	def engage_manual(self):
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
			self.manual_state.set("Manual Engaged!")
			self.in_manual = True

	def disengage_manual(self):
		self.status.set("Manual mode disengaged.")
		logger.info("Manual mode disengaged.")
		self.manual_state.set("Manual Disengaged.")
		self.in_manual = False

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

	def manual_set_valve(self):
		if self.in_manual:
			vc = Valve_Controller(self)
			commanding = vc.set_valve(self.set_valve.get())
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


### Utility Functions

def check_serial():
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

def system_health_check(app):
	app.details.set("Running through prechecks...")
	logger.info("Running through prechecks...")

	# check that everything is attached to serial ports

	# TODO change this to check for all serial connections and need to decide how I handle errors
	if not any(check_serial()):
		app.errors.set("ERROR: Serial connection issue.")
		return

	### Test Health of Controllers

	bc = Bath_Controller(app)
	if (bc.is_healthy() == True):
		# bath controller is healthy and can continue
		logger.debug("Bath Controller is healthy, moving forward.\n\n")
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
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "Valve Controller is unhealthy, stopping calibration.\n\n"
		app.errors.set(err_msg)
		logger.error(err_msg)
		return(False)

	pc = Pump_Controller()
	if (pc.is_healthy() == True):
		# pump controller is healthy and can continue
		logger.debug("Pump Controller is healthy, moving forward.\n\n")
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "Bath is unhealthy, stopping calibration.\n\n"
		app.errors.set(err_msg)
		logger.error(err_msg)
		return(False)

	cc = CalBoard_Controller()
	if (cc.is_healthy() == True):
		# calboard controller is healthy and can continue
		logger.debug("Calboard Controller is healthy, moving forward.\n\n")
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "Calboard is unhealthy, stopping calibration.\n\n"
		app.errors.set(err_msg)
		logger.error(err_msg)
		return(False)

	# MFCs controller

	# RGA controller

	# turbo pump controller

	# gc controller

	# fraction collector controller

	app.details.set("Precheck complete! System healthy.")
	logger.debug("Precheck complete! System healthy.")

	return(True)

### END Utility Functions


def calibrate_master(app):
	app.status.set("Calibration initiated.")
	logger.info("Calibration initiated.")
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

	data collection is turned on

	run through prechecks (manually call check_health by running prechecks)

	manually check FR level and click to refill if needed

	get solenoids into correct state

	get the loops up to their operational pressure
		HPLC turns on now
		MFCs turn on now

	"""

	cc.state_one() # put the calibration board into normal calibration operation state

	# turning on the HPLC TODO need to decide what this pressure limit is
	#pc.turn_on()
	#pc.set_pressure_limit(4000)

	# turning on the MFCs

	# operational values for queues
	#valve_queue 	= deque([1, 2, 3, 4, 5, 6])
	#temp_queue 		= deque([6, 4, 2])

	# testing values for queues
	valve_queue 	= deque([1, 2])
	temp_queue 		= deque([20.1, 20.2])


	# Boolean flags to inform calibrate_slave() about its proper state
	ready_for_pres_change 	= True 	# this starts True, and is reset True after last temp and sampling
	ready_for_temp_change	= False # this is set after pres change and after sampling
	waiting_for_temp 		= False	# this is set true when waiting for temp
	waiting_for_sample		= False	# this is set true after temp reached and before sampling is done
	app.currently_sampling 	= False # this is a temp solution until the real Sampling Controller is designed
	app.refilling_fr		= False # flag that is changed to True when FR refill button is pushed	

	calibrate_slave(app, bc, vc, pc, cc, valve_queue, temp_queue, ready_for_pres_change, ready_for_temp_change, waiting_for_temp, waiting_for_sample)

def calibrate_slave(app, bc, vc, pc, cc, valve_queue, temp_queue, ready_for_pres_change, ready_for_temp_change, waiting_for_temp, waiting_for_sample):
	
	# TODO need to think about what happens when a user assumes manual control and changes temp and pressure
		# will they actually do this during calibration?

	# test this entirely

	if app.paused:
		logger.debug("Calibration paused.")
		app.details.set("Calibration paused.")
	else:
		app.details.set("Calibration ongoing.")
		logger.debug("Calibration ongoing.")
		if ready_for_pres_change:
			logger.debug("Ready for pressure change.")
			# TODO do I need to check if the pressure is actually correct or just log it for data collection?
			vc.set_valve(valve_queue.popleft())
			logger.info("Pressure is: " + str(cc.read_press()))
			ready_for_pres_change = False
			ready_for_temp_change = True
		if ready_for_temp_change:
			logger.debug("Ready for temp change.")
			bc.change_temp(temp_queue.popleft())
			ready_for_temp_change = False
			waiting_for_temp = True
		if waiting_for_temp:
			logger.debug("Waiting for temp equilibration.")
			if(bc.check_temp()): # returns True if bath is at set_temp is met
				logger.debug("Temperature reached.")
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
