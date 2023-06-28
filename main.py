from redpitaya.lasercontrol import LaserControl
from redpitaya.mirrorcontrol import PositionTracker
from redpitaya.redpitaya_scpi import rpwrapper
import tkinter as tk
import time

# rp = rpwrapper("169.254.29.96")
# mirror = PositionTracker(100, rp)


class InteractiveWindow:
    def __init__(self, width, height, grid_size, decimation, distance):
        # Control objects
        self.rp = rpwrapper("169.254.29.96")
        self.laser = LaserControl(self.rp)
        self.mirror = PositionTracker(distance, self.rp)

        # Laser Parameters
        # self.laser.waveform = 'pwm'
        # self.laser.frequency = 10
        # self.laser.amplitude = 0.5
        # self.laser.duty_cycle = 0.01
        # self.laser.decimation = decimation


        # TODO: Add automatic window size calculation based on distance
        # UI elements
        self.width = width
        self.height = height
        self.grid_size = grid_size
        self.coordinates = []

        self.root = tk.Tk()
        self.root.title("Interactive Window")
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="white")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.record_coordinates)
        self.canvas.bind("<B1-Motion>", self.record_coordinates)

        self.coordinates_label = tk.Label(self.root, text="Current Coordinates: None")
        self.coordinates_label.pack()

        ### BUTTONS ###
        self.clear_button = tk.Button(self.root, text="Clear", command=self.clear_canvas)
        self.clear_button.pack()

        self.acquire_button = tk.Button(self.root, text="Acquire", command=self.acquire_plot)
        self.acquire_button.pack()

    def record_coordinates(self, event):
        x = event.x - (event.x % self.grid_size)
        y = event.y - (event.y % self.grid_size)
        # Convert to given grid
        x_grid = (abs(x - self.width)/10) * -1
        y_grid = abs(y - self.height)/10
        self.mirror.x = x_grid
        self.mirror.y = y_grid
        self.mirror.print_position()
        self.mirror.set_voltage()
        self.coordinates.append((x_grid, y_grid))
        self.canvas.create_rectangle(x, y, x + self.grid_size, y + self.grid_size, fill="black")
        self.update_coordinates_label(x_grid*-1, y_grid, self.mirror.voltages)

    def clear_canvas(self):
        self.canvas.delete("all")
        self.mirror.clear_coordinates()
        self.update_coordinates_label(None, None)

    def update_coordinates_label(self, x, y, voltages=None):
        if x is None or y is None:
            self.coordinates_label.config(text="Current Coordinates: None")
        else:
            self.coordinates_label.config(text=f"Current Coordinates: ({x}, {y}) \t Voltage_1 = {round(voltages[0],2)}, Voltage_2 = {round(voltages[1],2)}")

    ### DATA ACQUISITION ###
    def acquire_plot(self):
        self.laser.acquire()
        self.laser.plot()

    def start(self):
        self.root.mainloop()
        # TODO: make a function to configure with different parameters
        self.laser.configure()
        self.mirror.process_coordinates(self.coordinates)
    

decimation = 10
distance = 300
window = InteractiveWindow(400, 400, 10, decimation, distance)
window.start()
