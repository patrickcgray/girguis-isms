import serial
import time

serial_list = ['COM28']

class CalBoard_Controller():
	def __init__(self):
		self.ser = serial.Serial(serial_list[0], 9600, timeout=3)
		time.sleep(1)
		print("Starting Calibration Board Controller")
		print("Connected over serial at " + str(self.ser.name))

	def is_healthy(self):
		if (self.cmd_controller("?") == '1\r\n'):
			return(True)
		else:
			return(False)

	def cmd_controller(self, cmd):
		self.ser.write(b"" + cmd)
		ser_rsp = self.ser.readline()
		print("Output from Calibration Board Controller cmd: " + repr(ser_rsp))
		if ser_rsp == "F001\r\n":
			print("Error from Calibration Board Controller: " + repr(ser_rsp))
			return("bad cmd")
		else:
			return(ser_rsp)

	def turn_on(self):
		pass

	# these commands change the state of the solenoid valves on the calibration board
        def reset(self):
		# turning off all solenoid valves and putting back into startup state
		if self.cmd_controller("reset") == "reset\r\n":
			return True
		return False

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
	elif user_input == 8:
		cc.reset()
	elif user_input == -1:
		cc.ser.close()
		break
	else:
		print("didn't match option")




