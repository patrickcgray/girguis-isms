# girguis-isms

This code allows the Girguis Lab In-Situ Mass Spectrometer to be calibrated automatically before a deployment.


## Operation of the ISMS Calibration Station
Yeah we need to figure this out...

## File Overview
**calboard_sketch/calboard_sketch.ino** # sketch for the arduino connected to the Calibration Board  
**README.md**  # documentation  
**arduino_comm.py**  # test file for controlling arduino and commanding via python  
**calibrate_isms.py** # main control file for calibrating the mass spec  

## Tech Stack
#### Languages
* Python
   * Modules
      * Tkinter - Graphical Interface (Python interface to the TK GUI toolkit)
      * PySerial - access to serial comm functions
      
### Tested Environment (recommended)
* OSX
* python2

#### Setup
* pip install pyserial
* Required Support/Drivers
   * Drivers for serial devices
      * FTDI: http://www.ftdichip.com/FTDrivers.htm 
      * Prolific: http://www.prolific.com.tw/US/ShowProduct.aspx?p_id=229&pcid=41 
      
#### References
* Tkinter
   * https://wiki.python.org/moin/TkInter
   * https://docs.python.org/2/library/tkinter.html
   * http://www.tkdocs.com/tutorial/concepts.html
* PySerial
   * https://pythonhosted.org/pyserial/pyserial.html 
