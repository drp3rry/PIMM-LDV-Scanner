# import redpitaya_scpi as scpi
import time

class rpwrapper:
    def __init__(self, IP):
        self.IP = IP
        self.rp_s = scpi.scpi(IP)


    def setup_acquisition(self, waveform, frequency, amplitude, duty_cycle, periods, decimation):
        # Signal
        self.rp_s.tx_txt('GEN:RST')
        self.rp_s.tx_txt('SOUR1:FUNC ' + str(waveform).upper())
        self.rp_s.tx_txt('SOUR1:FREQ:FIX ' + str(frequency))
        self.rp_s.tx_txt('SOUR1:VOLT ' + str(amplitude/2))
        self.rp_s.tx_txt('SOUR1:DCYC ' + str(duty_cycle))
        self.rp_s.tx_txt('SOUR1:VOLT:OFFS ' + str(amplitude/2))
        # Acquisition
        self.rp_s.tx_txt('ACQ:DEC ' + str(decimation))
        ## TODO: Error handling
        return True

    def data_acquisition(self, decimation):
        sample_time = (16384/(125*10**6))*decimation
        self.rp_s.tx_txt('ACQ:START')
        self.rp_s.tx_txt('ACQ:TRIG AWG_PE')
        self.rp_s.tx_txt('OUTPUT1:STATE ON')
        self.rp_s.tx_txt('SOUR1:TRIG:INT')

        print("Waiting for trigger...")
        while 1:
            self.rp_s.tx_txt('ACQ:TRIG:STAT?')
            response = self.rp_s.rx_txt()
            if response == 'TD':
                time.sleep(0.1)
                break
        
        time.sleep(sample_time*5)
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

        return data_1, data_2
    
    def set_voltage(pin, voltage, print_voltage=False):
        self.rp_s.tx_txt('ANALOG:PIN AOUT'+str(pin)+',' + str(voltage))
        if print_voltage:
            print("Voltage setting for AO["+str(pin)+"] = "+str(voltage)+"V")
        return True