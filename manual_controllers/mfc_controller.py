import serial
import time


from calcCRC import calcCRC

serial_list = ['COM35']


class MFC_Controller_One():
	def __init__(self):
		self.ser = serial.Serial(serial_list[0], 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=3)
		time.sleep(1)
		print("Starting MFC Controller")
		print("Connected over serial at " + str(self.ser.name))
		self.turn_on()

	def is_healthy(self):
		# for the new SmartTrak 100 MFC_2
		#if ('Srnm210704\x8c\x92\r' in self.cmd_controller("?Srnm")):
		# max flow: Sinv200.400\xcd*\r

		# for the old SmartTrak 2 MFC_1
		if ('Srnm1380145\x93\r' in self.cmd_controller("?Srnm")):
		# max flow Sinv560.399\xf7\xae\r
			return(True)
		else:
			return(False)

	def read_streaming_state(self):
		self.cmd_controller('?Strm')

	def set_streaming_state(self, mode):
		self.cmd_controller('!Strm' + mode)

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

	def read_flow(self):
		self.cmd_controller("?Flow")

	def cmd_controller(self, cmd):
		crc = calcCRC(cmd)
		cmd = cmd + (crc) + '\x0d'
		print(cmd)
		self.ser.write(cmd)
		ser_rsp = self.ser.read(200)
		print("Output from MFC Controller cmd with repr(): " + repr(ser_rsp))
		print("Output from MFC Controller cmd *without* repr(): " + ser_rsp)
		return(ser_rsp)

	def turn_on(self):
		#self.set_streaming_state("Echo")
		pass

def check_health():
	mc = MFC_Controller_One()
	if (mc.is_healthy() == True):
		# calboard controller is healthy and can continue
		print("MFC Controller is healthy, moving forward.\n\n")
		return(True)
	else:
		# something is wrong and need to trip a pause and alarm and wait for user input
		err_msg = "MFC is unhealthy, stopping calibration.\n\n"
		print(err_msg)
		return(False)

def run_cmds():
	mc_1 = MFC_Controller_One()
	if mc_1.is_healthy():
		print("We're healthy!!!")
	#mc_1.set_gas(8)
	#mc_1.read_gas()
	#mc_1.set_setpoint(150)
	mc_1.read_flow()
	
run_cmds()


