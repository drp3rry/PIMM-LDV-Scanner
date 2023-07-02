# import redpitaya_scpi as scpi
import matplotlib.pyplot as plt
import time

class LaserControl:
    def __init__(self, redpitaya_object):
        self.waveform = 'pwm'
        self.frequency = 10
        self.amplitude = 0.5
        self.duty_cycle = 0.005
        self.decimation = 9
        self.rp = redpitaya_object
        self.reference_data = []
        self.response_data = []

    def configure(self):
        print("Configuring laser with parameters:")
        print(f"Waveform: {self.waveform}, Frequency: {self.frequency}, Amplitude: {self.amplitude}, Duty Cycle: {self.duty_cycle}, Decimation: {self.decimation}")
        self.rp.setup_acquisition(self.waveform, self.frequency, self.amplitude, self.duty_cycle, self.decimation)

    def acquire(self):
        self.response_data, self.reference_data = self.rp.data_acquisition(self.decimation)

    def plot(self):
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




    

    