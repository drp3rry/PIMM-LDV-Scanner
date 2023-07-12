import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd
import datetime

class DataManager:
    def __init__(self):
        self.experiment = None
        self.scan_path = []
        self.reference = []
        self.response_data = []
        self.frequency = 0
        self.decimation = 0
        self.waveform = ""
        self.laser_scale = 0
        self.sampling = 0
        self.dataframe = None
        # self.filename = "woodbeam-test"

    def save_data(self, as_text = False):
        filename = input("Enter filename: ")
        if as_text:
            with open("sample_data/experiments/"+filename+".txt", 'w') as f:
                data = {"scan_path": self.scan_path, "response_data": self.response_data,"reference": self.reference}
                f.write(str(data))
                f.close()
        ### SAVE AS PANDAS DATAFRAME
        else:
            data_columns = ['time_index', 'x', 'y', 'response']
            data_list = []
            time_index = np.arange(0, len(self.reference))
            for i in time_index:
                for j in range(len(self.scan_path)):
                    x = self.scan_path[j][0]
                    y = self.scan_path[j][1]
                    try:
                        response = self.response_data[j][i]
                    except:
                        response = 0
                    data_list.append([i, x, y, response])
            data_df = pd.DataFrame(data_list, columns=data_columns)
            data_df.to_pickle("sample_data/experiments/"+filename+".pkl")
        ### SAVE EXPERIMENT DETAILS
        experiment_details_path = "sample_data/experiments/experiment_details.csv"
        try:
            ### Read experiment details
            experiment_details_df = pd.read_csv(experiment_details_path)
            ### Append new experiment details
            experiment_details_df = experiment_details_df.append({"filename": filename, "frequency": self.frequency, "decimation": self.decimation, "date": datetime.datetime.now(), "waveform": self.waveform, "laser_scale": self.laser_scale, "sampling": self.sampling}, ignore_index=True)
            ### Save experiment details
            experiment_details_df.to_csv(experiment_details_path, index=False)
        except Exception as e:
            print("Error saving experiment details: " + str(e))
    
    def add_scan(self, reference, response):
        ## Response duration 
        sampling_rate = 125000000
        period_length = (1/self.frequency)/(self.decimation/sampling_rate)
        print("Length of scan data (pre-cleaning): " + str(len(response)) + " samples")
        print("Cleaning scan data...")
        ## Clean scan data
        try:
            for i in range(len(reference)):
                if reference[i] > 0.1:
                    impulse_start = i
                    break
            reference = reference[impulse_start-1:impulse_start+int(period_length)]
            response = response[impulse_start-1:impulse_start+int(period_length)]
            print("Length of scan data (post-cleaning): " + str(len(response)) + " samples")
        except:
            print("ERR: Scan data is not clean")
            # make response list of zeros length of self.reference
            response = [0 for i in range(len(self.reference))]

        ## If reference is empty, set reference
        if len(self.reference) == 0:
            self.reference = reference
        
        ## Append response data
        self.response_data.append(response)

    def read_pickle(self, filename):
        self.dataframe = pd.read_pickle(filename)


        
class Visualizor:
    def __init__(self, scan_path, response_data):
        self.scan_path = scan_path
        self.response_data = response_data
        self.x_values = list(set([x[0] for x in self.scan_path]))
        self.y_values = list(set([x[1] for x in self.scan_path]))
        self.response = np.zeros((len(self.x_values), len(self.y_values)))
        ## shortest scan
        self.num_frames = min([len(x) for x in self.response_data])
        self.fps = 500
        self.im = plt.imshow(self.response, cmap='hot', interpolation='nearest', vmin=-1, vmax=1)
        self.title = plt.title(f"Index: {0} of {self.num_frames}")

    
    def get_response_at_time(self, time):
        data_array = np.zeros((len(self.x_values), len(self.y_values)))
        for i, coordinate in enumerate(self.scan_path):
            # print(i)
            # print(coordinate)
            grid_index = (self.x_values.index(coordinate[0]), self.y_values.index(coordinate[1]))
            # print(grid_index)
            x, y = grid_index
            # print(x, y)
            data_array[x, y] = self.response_data[i][time]
        return data_array

    def heatmap(self):
        print("Setting up animation...")
        fig = plt.figure()
        self.response = self.get_response_at_time(0)
        self.im = plt.imshow(self.response, cmap='hot', interpolation='nearest', vmin=-1, vmax=1)
        self.title = plt.title(f"Index: {0} of {self.num_frames}")
        plt.colorbar()

        plt.close('all')
        print("Animating data...")
        anim = animation.FuncAnimation(fig, self.animate_heatmap, frames=self.num_frames, interval=1000/self.fps, blit=True, repeat=False)
        anim.save('animation.mp4', fps=self.fps, extra_args=['-vcodec', 'libx264'])
        print("Animation saved to animation.mp4")

    def animate_heatmap(self, time):
        time += 1
        self.response = self.get_response_at_time(time)
        self.im.set_data(self.response)
        self.title.set_text(f"Index: {time} of {self.num_frames}")
        return [self.im, self.title]
    

