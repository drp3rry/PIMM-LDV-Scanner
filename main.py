from redpitaya.lasercontrol import LaserControl
from redpitaya.mirrorcontrol import PositionTracker
from redpitaya.redpitaya_scpi import rpwrapper
from redpitaya.redpitaya_scpi import rpwrapperTest
from datamanager.visualization import DataManager
import tkinter as tk
import time
import ast

# rp = rpwrapper("169.254.29.96")
# mirror = PositionTracker(100, rp)


class InteractiveWindow:
    def __init__(self, width, height, grid_size, distance, mode_test=False):
        ### Control objects
        if mode_test:
            self.rp = rpwrapperTest()
        else:
            self.rp = rpwrapper("169.254.29.96")

        self.laser = LaserControl(self.rp)
        self.mirror = PositionTracker(distance, self.rp)
        self.data = DataManager()

        # Laser Parameters
        # self.laser.waveform = 'pwm'
        # self.laser.frequency = 10
        # self.laser.amplitude = 0.5
        # self.laser.duty_cycle = 0.01
        # self.laser.decimation = decimation

        ### Scanning parameters
        self.topleft = (None,None)
        self.topright = (None,None)
        self.bottomleft = (None,None)
        self.bottomright = (None,None)
        self.paint_next = "set top left"
        self.scanning_points = []


        # TODO: Add automatic window size calculation based on distance
        ### UI elements
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.coordinates = []
        self.tkx = 0
        self.tky = 0


        self.root = tk.Tk()
        self.root.title("Interactive Window")
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="white")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.record_coordinates)
        self.canvas.bind("<B1-Motion>", self.record_coordinates)

        self.coordinates_label = tk.Label(self.root, text="Current Coordinates: None")
        self.coordinates_label.pack()

        ### BUTTONS ###
        self.buttonframe = tk.Frame(self.root)
        self.clear_button = tk.Button(self.root, text="Clear", command=self.clear_canvas)
        self.clear_button.pack()

        self.paint_button = tk.Button(self.root, text=f"Set: {self.paint_next}", command=self.paint_object)
        self.paint_button.pack()

        self.configure_button = tk.Button(self.root, text="Configure", command=self.configure_laser)
        self.configure_button.pack()

        self.acquire_button = tk.Button(self.root, text="Acquire", command=self.acquire_single_plot)
        self.acquire_button.pack()

        self.scan_button = tk.Button(self.root, text="Scan Object", command=self.scan_object)
        self.scan_button.pack()

        self.save_button = tk.Button(self.root, text="Save data", command=self.save_data)
        self.save_button.pack()

        self.load_button = tk.Button(self.root, text="Save current configuration", command=self.save_configuration)
        self.load_button.pack()

        self.load_button = tk.Button(self.root, text="Load saved configuration", command=self.load_configuration)
        self.load_button.pack()

    def record_coordinates(self, event):
        self.tkx = event.x - (event.x % self.grid_size)
        self.tky = event.y - (event.y % self.grid_size)
        # Convert to given grid
        # x_grid = (abs(self.tkx - self.width)/10) * -1
        # y_grid = abs(self.tky - self.height)/10
        # self.mirror.x = x_grid
        # self.mirror.y = y_grid
        self.mirror.x, self.mirror.y = self.get_physical_coordinates(self.tkx, self.tky)
        self.mirror.print_position()
        self.mirror.set_voltage(msg = False)
        self.coordinates.append((self.mirror.x, self.mirror.y))
        self.canvas.create_rectangle(self.tkx, self.tky, self.tkx + self.grid_size, self.tky + self.grid_size, fill="black")
        self.update_coordinates_label(self.mirror.x, self.mirror.y, self.mirror.voltages)
        ### update vertex corners

    def get_physical_coordinates(self, x, y):
        x_actual = (abs(x - self.width)/self.grid_size) * -1
        y_actual = abs(y - self.height)/self.grid_size
        return x_actual, y_actual
    

    def clear_canvas(self):
        self.canvas.delete("all")
        self.mirror.clear_coordinates()
        self.update_coordinates_label(None, None)
        self.bottomleft = (None,None)
        self.bottomright = (None,None)
        self.topleft = (None,None)
        self.topright = (None,None)
        self.paint_next = "set top left"
        self.paint_button.config(text=f"Set: {self.paint_next}")

    def update_coordinates_label(self, x, y, voltages=None):
        if x is None or y is None:
            self.coordinates_label.config(text="Current Coordinates: None")
        else:
            self.coordinates_label.config(text=f"Current Coordinates: ({x}, {y}) \t Voltage_1 = {round(voltages[0],2)}, Voltage_2 = {round(voltages[1],2)}")

    ### DATA ACQUISITION ###
    def configure_laser(self):
        self.laser.configure()

    def acquire_single_plot(self):
        self.laser.acquire()
        self.laser.plot()
    
    def save_data(self):
        name = input("Enter a name for the data: ")
        self.laser.save_data(name)
        
    def save_configuration(self):
        ## Enter name of configuration file
        name = input("Enter a name for the configuration: ")
        ## Save configuration as dictionary
        config = {"topleft": self.topleft, "topright": self.topright, "bottomleft": self.bottomleft, "bottomright": self.bottomright}
        with open ("sample_data/configurations/" + name + ".txt", "w") as f:
            f.write(str(config))
            f.close()


    def load_configuration(self):
        ## Enter name of configuration file
        try:
            name = input("Enter a name for the configuration: ")
            with open ("sample_data/configurations/" + name + ".txt", "r") as f:
                config = ast.literal_eval(f.read())
                f.close()
            ## Set class variables to configuration, prepare the button for next step
            self.topleft = config["topleft"]
            self.topright = config["topright"]
            self.bottomleft = config["bottomleft"]
            self.bottomright = config["bottomright"]
            self.paint_next = "draw object outline"
            self.paint_button.config(text=f"Set: {self.paint_next}")
            print("Configuration loaded")
        except:
            print("Configuration loading failed")

       
    def paint_object(self):
        # TODO: Create a mapping function from tk grid to actual real life grid
        ### Iterate over vertices
        if self.topleft == (None, None):
            self.topleft = (self.tkx, self.tky)
            self.canvas.create_rectangle(self.topleft[0], self.topleft[1], self.topleft[0] + self.grid_size, self.topleft[1] + self.grid_size, fill="blue")
            self.paint_next = "set top right"
            print(self.topleft)
        elif self.topright == (None, None):
            self.topright = (self.tkx, self.tky)
            self.canvas.create_rectangle(self.topright[0], self.topright[1], self.topright[0] + self.grid_size, self.topright[1] + self.grid_size, fill="blue")
            self.paint_next = "set bottom right"
            print(self.topright)
        elif self.bottomright == (None, None):
            self.bottomright = (self.tkx, self.tky)
            self.canvas.create_rectangle(self.bottomright[0], self.bottomright[1], self.bottomright[0] + self.grid_size, self.bottomright[1] + self.grid_size, fill="blue")
            self.paint_next = "set bottom left"
            print(self.bottomright)
        elif self.bottomleft == (None, None):
            self.bottomleft = (self.tkx, self.tky)
            self.canvas.create_rectangle(self.bottomleft[0], self.bottomleft[1], self.bottomleft[0] + self.grid_size, self.bottomleft[1] + self.grid_size, fill="blue")
            self.paint_next = "draw object outline"
            print(self.bottomleft)
        ## Create a box
        elif self.paint_next == "draw object outline":
            # self.canvas.create_polygon(self.topleft, self.topright, self.bottomright, self.bottomleft,fill="red", outline="blue")
            self.canvas.create_polygon(self.topleft[0], self.topleft[1], self.topright[0]+self.grid_size, self.topright[1], self.bottomright[0]+self.grid_size, self.bottomright[1]+self.grid_size, self.bottomleft[0], self.bottomleft[1]+self.grid_size,fill="red", outline="blue")
            self.paint_next = "Ready to Scan"

        self.paint_button.config(text=f"Set: {self.paint_next}")
        return True
    
    def scan_object(self):
        ### CHECKS
        if self.paint_next != "Ready to Scan":
            print("Scanning object not set")
            return False
        ### Scan object: get coordinates
        ## Bounding box: be cautious and set to smallest box
        print("Determining scan points..")
        left = max(self.topleft[0], self.bottomleft[0])
        top = max(self.topleft[1], self.topright[1])
        right = min(self.topright[0]+self.grid_size, self.bottomright[0]+self.grid_size)
        bottom = min(self.bottomleft[1]+self.grid_size, self.bottomright[1]+self.grid_size)
        # Create a list of scanning points
        self.scanning_points = []
        for y in range(top, bottom, self.grid_size):
            for x in range(left, right, self.grid_size):
                self.scanning_points += [(x, y)]
        ## save scanning points in data object
        self.data.scan_path = self.scanning_points
        
        ### Iterate over scanning points
        print("Starting scan..")
        ## Configure laser
        self.laser.configure()
        for i in self.scanning_points:
            ### Draw yellow box
            self.canvas.create_rectangle(i[0], i[1], i[0] + self.grid_size, i[1] + self.grid_size, fill="yellow")
            ### Set mirror location
            self.mirror.x, self.mirror.y = self.get_physical_coordinates(i[0], i[1])
            self.mirror.set_voltage()
            
            ### Fire laser
            self.laser.acquire()
            ## Display plot for first 5 scans
            if self.scanning_points.index(i) < 5:
                self.laser.plot()

            ### Save data
            self.data.add_scan(self.laser.reference_data, self.laser.response_data)
            ### Draw green box
            self.canvas.create_rectangle(i[0], i[1], i[0] + self.grid_size, i[1] + self.grid_size, fill="green")
            ### Wait to separate scans
            time.sleep(0.005)
            
        ### Save data
        self.data.save_data()


    def start(self):
        self.root.mainloop()
        # TODO: make a function to configure with different parameters
        # self.laser.configure()
        self.mirror.process_coordinates(self.coordinates, msg = False)
    

# decimation = 10
distance = 400
window = InteractiveWindow(500, 500, 10, distance, mode_test=False)
window.start()
