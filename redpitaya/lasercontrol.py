# import redpitaya_scpi as scpi

class lasercontrol:
    def __init__(self):
        self.waveform = 'pwm'
        self.frequency = 10
        self.amplitude = 0.5
        self.duty_cycle = 0.01
        self.periods = 20
        self.decimation = 10

    def hello(self):
        print("Hello from lasercontrol")



    

    