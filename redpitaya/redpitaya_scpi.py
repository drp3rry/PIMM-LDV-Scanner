import socket

class rpwrapper:
    def __init__(self, IP):
        self.IP = IP
        self.rp_s = scpi(IP)


    def set_voltage(self, pin, voltage, print_voltage=False):
        self.rp_s.tx_txt('ANALOG:PIN AOUT'+str(pin)+',' + str(voltage))
        if print_voltage:
            print("Voltage setting for AO["+str(pin)+"] = "+str(voltage)+"V")
        return True

    def setup_burst(self, waveform, frequency, amplitude, duty_cycle, decimation):
        # Signal
        self.rp_s.tx_txt('GEN:RST')
        self.rp_s.tx_txt('SOUR1:FUNC ' + str(waveform).upper())
        self.rp_s.tx_txt('SOUR1:FREQ:FIX ' + str(frequency))
        self.rp_s.tx_txt('SOUR1:VOLT ' + str(amplitude/2))
        self.rp_s.tx_txt('SOUR1:DCYC ' + str(duty_cycle))
        self.rp_s.tx_txt('SOUR1:VOLT:OFFS ' + str(amplitude/2))

        self.rp_s.tx_txt('SOUR1:BURS:STAT BURST')                
        self.rp_s.tx_txt('SOUR1:BURS:NOR ' + str(1)) 
        # Acquisition
        self.rp_s.tx_txt('ACQ:DEC ' + str(decimation))
        self.rp_s.tx_txt('ACQ:TRIG:DLY 8192')
        ## TODO: Error handling
        return True
    
    def acquire_burst(self, sample_time, frequency):
        print("setup and start")
        ### Setup acquisition, send reference
        self.rp_s.tx_txt('ACQ:START')
        self.rp_s.tx_txt('ACQ:TRIG NOW')
        self.rp_s.tx_txt('OUTPUT1:STATE ON')
        self.rp_s.tx_txt('SOUR1:TRIG:INT')
        
        ### Wait for trigger response loop
        while 1:
            self.rp_s.tx_txt('ACQ:TRIG:STAT?')
            if self.rp_s.rx_txt() == 'TD':
                ### Sleep at least the length of buffer
                time.sleep(sample_time*3)
                break
        ## Read data (call twice)
        self.rp_s.tx_txt('ACQ:SOUR1:DATA?')            
        data_string_1 = self.rp_s.rx_txt() 
        print(data_string_1[:100]) #Print included for debugging but useful to verify data acquistion is working
        self.rp_s.tx_txt('ACQ:SOUR2:DATA?')
        data_string_2 = self.rp_s.rx_txt() 
        print(data_string_2[:100])   
    
        self.rp_s.tx_txt('ACQ:SOUR1:DATA?')             
        data_string_1 = self.rp_s.rx_txt() 
        print(data_string_1[:100])
        self.rp_s.tx_txt('ACQ:SOUR2:DATA?')
        data_string_2 = self.rp_s.rx_txt()  
        print(data_string_2[:100])

        try:
            data_string_1 = data_string_1.strip('{}\n\r').replace("  ", "").split(',')
            data_1 = list(map(float, data_string_1))     
            data_string_2 = data_string_2.strip('{}\n\r').replace("  ", "").split(',')
            data_2 = list(map(float, data_string_2))
        except Exception as e:
            print(f"Error reading buffer: {e}")
            data_1, data_2 = [0], [0]

        ### Turn off
        self.rp_s.tx_txt('ACQ:STOP')
        self.rp_s.tx_txt('OUTPUT1:STATE OFF')

        return data_1, data_2


    ### UNUSED FUNCTION
    def read_buffer(self):
        self.rp_s.tx_txt('ACQ:SOUR1:DATA?')            
        data_string_1 = self.rp_s.rx_txt() 
        self.rp_s.tx_txt('ACQ:SOUR2:DATA?')
        data_string_2 = self.rp_s.rx_txt()    
        
        self.rp_s.tx_txt('ACQ:SOUR1:DATA?')             
        data_string_1 = self.rp_s.rx_txt() 
        self.rp_s.tx_txt('ACQ:SOUR2:DATA?')
        data_string_2 = self.rp_s.rx_txt()  

    
        data_string_1 = data_string_1.strip('{}\n\r').replace("  ", "").split(',')
        # print(data_string_1)
        data_1 = list(map(float, data_string_1))     
        data_string_2 = data_string_2.strip('{}\n\r').replace("  ", "").split(',')
        data_2 = list(map(float, data_string_2))
        return data_1, data_2

    ### ALL FOLLOWING FUNCTIONS USED FOR NON BURST SETUP
    def setup_acquisition(self, waveform, frequency, amplitude, duty_cycle, decimation):
        # Signal
        self.rp_s.tx_txt('GEN:RST')
        self.rp_s.tx_txt('SOUR1:FUNC ' + str(waveform).upper())
        self.rp_s.tx_txt('SOUR1:FREQ:FIX ' + str(frequency))
        self.rp_s.tx_txt('SOUR1:VOLT ' + str(amplitude/2))
        self.rp_s.tx_txt('SOUR1:DCYC ' + str(duty_cycle))
        self.rp_s.tx_txt('SOUR1:VOLT:OFFS ' + str(amplitude/2))
        # Acquisition
        self.rp_s.tx_txt('ACQ:DEC ' + str(decimation))
        self.rp_s.tx_txt('ACQ:TRIG:DLY 8192')
        ## TODO: Error handling
        return True

    def reference_start(self):
        self.rp_s.tx_txt('OUTPUT1:STATE ON')
        self.rp_s.tx_txt('SOUR1:TRIG:INT')

    def reference_stop(self):
        self.rp_s.tx_txt('OUTPUT1:STATE OFF')

    def acquisition_start(self):
        self.rp_s.tx_txt('ACQ:START')
        self.rp_s.tx_txt('ACQ:TRIG CH2_PE')
        return True
    
    def acquisition_stop(self):
        self.rp_s.tx_txt('ACQ:STOP')
        # self.rp_s.tx_txt('OUTPUT1:STATE OFF')
        return True
    
    def data_acquisition(self, sample_time, frequency):

        time.sleep(2*frequency)
        print("Waiting for trigger...")
        while 1:
            self.rp_s.tx_txt('ACQ:TRIG:STAT?')
            response = self.rp_s.rx_txt()
            if response == 'TD':
                time.sleep(sample_time)
                break
        
        # time.sleep(sample_time*2)
        time.sleep(2*frequency)
        # read source 1
    

        self.rp_s.tx_txt('ACQ:SOUR1:DATA?')            
        data_string_1 = self.rp_s.rx_txt() 
        self.rp_s.tx_txt('ACQ:SOUR2:DATA?')
        data_string_2 = self.rp_s.rx_txt()    
        
        # read source 2
        self.rp_s.tx_txt('ACQ:SOUR1:DATA?')             
        data_string_1 = self.rp_s.rx_txt() 
        self.rp_s.tx_txt('ACQ:SOUR2:DATA?')
        data_string_2 = self.rp_s.rx_txt()  

    
        data_string_1 = data_string_1.strip('{}\n\r').replace("  ", "").split(',')
        data_1 = list(map(float, data_string_1))     
        data_string_2 = data_string_2.strip('{}\n\r').replace("  ", "").split(',')
        data_2 = list(map(float, data_string_2))

        # print(data_1[:20])

        # # stop acquisition
        # self.rp_s.tx_txt('ACQ:STOP')
        # self.rp_s.tx_txt('OUTPUT1:STATE OFF')
        return data_1, data_2
    

    
### Class used for program functionality when Red Pitaya is not connected
class rpwrapperTest:
    def __init__(self):
        self.rp_s = True

    def setup_acquisition(self, waveform, frequency, amplitude, duty_cycle, decimation):
        print("TEST: ACQUISITION SETUP")
        return True
    def data_acquisition(self, decimation):
        print("TEST: ACQUISITION")
        return (True, True)
    def set_voltage(self, pin, voltage, print_voltage=False):
        # print("TEST: SET VOLTAGE")
        return True




"""SCPI access to Red Pitaya."""

__author__ = "Luka Golinar, Iztok Jeras"
__copyright__ = "Copyright 2015, Red Pitaya"

class scpi (object):
    """SCPI class used to access Red Pitaya over an IP network."""
    delimiter = '\r\n'

    def __init__(self, host, timeout=None, port=5000):
        """Initialize object and open IP connection.
        Host IP should be a string in parentheses, like '192.168.1.100'.
        """
        self.host    = host
        self.port    = port
        self.timeout = timeout

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if timeout is not None:
                self._socket.settimeout(timeout)

            self._socket.connect((host, port))

        except socket.error as e:
            print('SCPI >> connect({!s:s}:{:d}) failed: {!s:s}'.format(host, port, e))

    def __del__(self):
        if self._socket is not None:
            self._socket.close()
        self._socket = None

    def close(self):
        """Close IP connection."""
        self.__del__()

    def rx_txt(self, chunksize = 4096):
        """Receive text string and return it after removing the delimiter."""
        msg = ''
        while 1:
            chunk = self._socket.recv(chunksize).decode('utf-8') # Receive chunk size of 2^n preferably
            msg += chunk
            if (len(msg) and msg[-2:] == self.delimiter):
                break
        return msg[:-2]

    def rx_arb(self):
        numOfBytes = 0
        """ Recieve binary data from scpi server"""
        str=b''
        while (len(str) != 1):
            str = (self._socket.recv(1))
        if not (str == b'#'):
            return False
        str=b''
        while (len(str) != 1):
            str = (self._socket.recv(1))
        numOfNumBytes = int(str)
        if not (numOfNumBytes > 0):
            return False
        str=b''
        while (len(str) != numOfNumBytes):
            str += (self._socket.recv(1))
        numOfBytes = int(str)
        str=b''
        while (len(str) != numOfBytes):
            str += (self._socket.recv(4096))
        return str

    def tx_txt(self, msg):
        """Send text string ending and append delimiter."""
        return self._socket.sendall((msg + self.delimiter).encode('utf-8')) # was send(().encode('utf-8'))

    def txrx_txt(self, msg):
        """Send/receive text string."""
        self.tx_txt(msg)
        return self.rx_txt()

# IEEE Mandated Commands

    def cls(self):
        """Clear Status Command"""
        return self.tx_txt('*CLS')

    def ese(self, value: int):
        """Standard Event Status Enable Command"""
        return self.tx_txt('*ESE {}'.format(value))

    def ese_q(self):
        """Standard Event Status Enable Query"""
        return self.txrx_txt('*ESE?')

    def esr_q(self):
        """Standard Event Status Register Query"""
        return self.txrx_txt('*ESR?')

    def idn_q(self):
        """Identification Query"""
        return self.txrx_txt('*IDN?')

    def opc(self):
        """Operation Complete Command"""
        return self.tx_txt('*OPC')

    def opc_q(self):
        """Operation Complete Query"""
        return self.txrx_txt('*OPC?')

    def rst(self):
        """Reset Command"""
        return self.tx_txt('*RST')

    def sre(self):
        """Service Request Enable Command"""
        return self.tx_txt('*SRE')

    def sre_q(self):
        """Service Request Enable Query"""
        return self.txrx_txt('*SRE?')

    def stb_q(self):
        """Read Status Byte Query"""
        return self.txrx_txt('*STB?')

# :SYSTem

    def err_c(self):
        """Error count."""
        return self.txrx_txt('SYST:ERR:COUN?')

    def err_c(self):
        """Error next."""
        return self.txrx_txt('SYST:ERR:NEXT?')
    

import time


