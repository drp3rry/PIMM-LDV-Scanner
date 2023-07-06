# import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import time

class LaserControl:
    def __init__(self, redpitaya_object):
        self.waveform = 'pwm'
        self.frequency = 1
        self.amplitude = 1
        self.duty_cycle = 0.001
        self.decimation = 9
        self.sample_time = (16384/(125*10**6))*self.decimation
        self.rp = redpitaya_object
        self.reference_data = []
        self.response_data = []

    def configure(self):
        print("Configuring laser with parameters:")
        print(f"Waveform: {self.waveform}, Frequency: {self.frequency}, Amplitude: {self.amplitude}, Duty Cycle: {self.duty_cycle}, Decimation: {self.decimation}")
        self.rp.setup_acquisition(self.waveform, self.frequency, self.amplitude, self.duty_cycle, self.decimation)

    def start(self):
        # self.rp.acquisition_start()
        # print("Acquisition started")
        self.rp.reference_start()
    
    def stop(self):
        # self.rp.acquisition_stop()
        # print("Acquisition stopped")
        self.rp.reference_stop()

    def acquire(self):
        self.rp.acquisition_start()
        self.response_data, self.reference_data = self.rp.data_acquisition(self.sample_time, self.frequency)
        self.rp.acquisition_stop()
        return True
        # clear existing data
        # self.reference_data, self.response_data = [], []
        # # acquire new data
        # while len(self.reference_data) == 0:
        #     print("Data is empty, acquiring new data...")
        #     self.reference_data, self.response_data = self.rp.data_acquisition(self.sample_time, self.frequency)
        # return True

    def plot(self, clear = False):
        if clear:
            plt.clf()
        plt.plot(self.reference_data, label='Reference')
        plt.plot(self.response_data, label='Response')
        plt.legend()
        plt.show()

    def save_data(self, filepath):
        # TODO - Add location of scan
        # Create dictionary of parameters
        with open("sample_data/"+filepath+".txt", 'w') as f:
            data = {"Waveform": self.waveform, "Frequency": self.frequency, "Amplitude": self.amplitude, "Duty Cycle": self.duty_cycle, "Decimation": self.decimation, "Reference Data": self.reference_data, "Response Data": self.response_data}
            f.write(str(data))
            f.close()
        # with open("sample_data/"+filepath+"_reference.txt", 'w') as f:
        #     data = {"Waveform": self.waveform, "Frequency": self.frequency, "Amplitude": self.amplitude, "Duty Cycle": self.duty_cycle, "Decimation": self.decimation, }

        #     f.write(f"Reference Data: {self.reference_data}")
        #     f.close()
        # with open("sample_data/"+filepath+"_response.txt", 'w') as f:
        #     f.write(f"Response Data: {self.response_data}")
        #     f.close()

    
    
    def test_scan(self):
        return True




    

    