# main.py
# Establishes local SCPI connection to Redpitaya
# Initialize PyQT application

import redpitaya_scpi_core as scpi
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow


def main():

    IP = 'rp-f06d1a.local' # or http://192.168.9.10/
    rp = scpi.scpi(IP)
    rp_setup(rp)

    app = QApplication([])
    window = MainWindow(rp)
    window.show()
    app.exec_()  
    #MainWindow.closeEvent() is called when app is closed

    
def rp_setup(rp):
    # Reset signal generator and acquisition

    rp.tx_txt('GEN:RST')
    rp.tx_txt('ACQ:RST')

    rp.tx_txt('ACQ:DATA:FORMAT BIN')
    rp.tx_txt('ACQ:DATA:UNITS RAW')
    rp.tx_txt('ACQ:DEC 128')            # 125/128 = 0.97 MSa/s
    rp.tx_txt('ACQ:TRIG:LEV 0')
    rp.tx_txt('ACQ:TRIG:DLY 8192')

    rp.tx_txt('SOUR1:FUNC SINE')        # sine function
    rp.tx_txt('SOUR1:FREQ:FIX 1000')    # 1 khz
    rp.tx_txt('SOUR1:VOLT 1')           # amplitude 1v
    
    rp.tx_txt('SOUR2:FUNC SQUARE')      # square function
    rp.tx_txt('SOUR2:FREQ:FIX 1000')    # 1 khz
    rp.tx_txt('SOUR2:VOLT 1')           # amplitude 1v
    
    rp.tx_txt('SOUR:TRIG:INT')
    rp.tx_txt('PHAS:ALIGN')
    rp.tx_txt('OUTPUT:STATE ON')
   
if __name__ == "__main__":
    main()
    