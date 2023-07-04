import matplotlib.pyplot as plt
import numpy as np



class DataManager:
    def __init__(self):
        self.experiment = None
        self.scan_path = []
        self.reference = []
        self.response_data = []

    def save_data(self):
        filename = input("Enter filename: ")
        with open("sample_data/experiments/"+filename+".txt", 'w') as f:
            data = {"scan_path": self.scan_path, "response_data": self.response_data,"reference": self.reference}
            f.write(str(data))
            f.close()

    def add_scan(self, reference, response):
        ## Clean scan data
        for i in range(len(reference)):
            if reference[i] > 0.1:
                impulse_start = i
                break
        reference = reference[impulse_start-1:]
        response = response[impulse_start-1:]

        ## If reference is empty, set reference
        if len(self.reference) == 0:
            self.reference = reference
        
        ## Append response data
        self.response_data.append(response)

        
# class Visualizor:
#     def __init__(self, data_manager):
#         self.data_manager = data_manager
#         self.x_values = []
#         self.y_values = []
    
#     def get_response_at_time(self, time):

