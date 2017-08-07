# girguis-isms

This code allows the Girguis Lab In-Situ Mass Spectrometer to be calibrated automatically before a deployment.

## File Overview
**README.md**  # documentation  
**calboard_sketch/calboard_sketch.ino** # sketch for the arduino connected to the Calibration Board  
**manual_controllers/** # simplified controllers to allow manual commanding and testing of all devices  
**arduino_comm.py**  # test file for controlling arduino and commanding via python  
**calibrate_isms.py** # main control file for calibrating the mass spec  
**calcCRC.py** # simple python script to calculate the checksum required for serial comm with the MFCs  

## Hardware:
*  1x Temp Bath - Thermo Scientific Temperature Bath
*  1x HPLC Pump - ChromTech Dual Piston HPLC Pump
*  1x Arduino  - standard Arduino Mega 2560 for controlling the calibration board
*  1x Calibration Board - custom setup with two high pressure loops for and one low pressure loop that simulations the deep sea pressure and gas environment allowing for calibration of the ISMS inlet
*  2x Mass Flow Controllers - Sierra Instruments SmartTrak Series 100 Mass Flow Controller
*  1x Valco 6-Port Valve - Valco Instruments 6-Port Valve Actuators

## Tech Stack
* Python
   * Modules
      * Tkinter - Graphical Interface (Python interface to the TK GUI toolkit)
      * PySerial - access to serial comm functions
      
### Tested Environments (recommended)
* OSX or Windows 7

### Tested Python Versions
* python27

## Setup
* On OSX
   * pip install pyserial
   * Required Support/Drivers
      * Drivers for serial devices
         * FTDI: http://www.ftdichip.com/FTDrivers.htm 
         * Prolific: http://www.prolific.com.tw/US/ShowProduct.aspx?p_id=229&pcid=41 
         
* For clean Windows 7 Setup
   * Install python 2.7.x https://www.python.org/downloads/windows/ 
      * Open command prompt
      * Navigate to the directory where python is installed (default C:/Python27)
      * Run the command python ‘python -m pip install pyserial’
   * Install git https://git-scm.com/download/win
      * Use all default settings
      * Open Git GUI 
         * Clone from https://github.com/patrickcgray/girguis-isms.git
      * OR from git bash
         * Type ‘git clone https://github.com/patrickcgray/girguis-isms.git’
   * Required Drivers
      * For all devices connected using this cable for this cable https://www.sabrent.com/product/SBT-USC1M/usb-serial-cable-adapter/ Type ‘SBT-USC1M’ into this page to get rs232-usb cable drivers https://www.sabrent.com/downloads/?wpdmc=windows-drivers 
      * For HPLC Pump
         * Navigate to https://ssihplc.com/manuals/#driver-downloads and download ‘NXP Virtual COM port USB drivers (Micro USB)’
      
#### References
* Tkinter
   * https://wiki.python.org/moin/TkInter
   * https://docs.python.org/2/library/tkinter.html
   * http://www.tkdocs.com/tutorial/concepts.html
* PySerial
   * https://pythonhosted.org/pyserial/pyserial.html 
