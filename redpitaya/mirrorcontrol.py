from scipy.optimize import fsolve
# import rphelper as rph
import numpy as np

def y_equation(alpha, gamma, d, y_value):
    return (-2*d*np.cos(2*alpha) + 15.705*np.sin(2*alpha - 2*gamma) - 15.705*np.sin(2*alpha + 2*gamma) - 7.65*np.cos(2*alpha) + 3.825*np.cos(2*alpha - 2*gamma) + 3.825*np.cos(2*alpha + 2*gamma))/(np.cos(-2*alpha + 2*gamma + 0.184044969622802) - np.cos(2*alpha + 2*gamma + 0.184044969622802)) - y_value

def z_equation(gamma, d, z_value):
    return (-d*np.cos(gamma) - d*np.cos(3*gamma + 0.368089939245604) + 15.705*np.sin(gamma + 0.368089939245604) + 15.705*np.sin(3*gamma + 0.368089939245604) + 3.825*np.cos(gamma + 0.368089939245604) - 3.825*np.cos(3*gamma + 0.368089939245604))/(np.sin(gamma) + np.sin(3*gamma + 0.368089939245604)) - z_value

### Legacy: Moved into class
# def mirror_solve(target, distance):
#     # Initial guess for the solution
#     initial_guess = np.pi/4
#     # Correct for the z axis offset
#     target = (target[0], target[1] + 27.5)

#     # For conversion to voltage
#     alpha_voltage_0 = 45
#     gamma_voltage_0 = 40

#     # Solve the equation numerically
#     gamma_solution = fsolve(z_equation, initial_guess, args=(distance, target[1]))
#     alpha_solution = fsolve(y_equation, initial_guess, args=(target[0], gamma_solution, distance))

#     alpha_voltage = (alpha_solution[0]*180/np.pi - alpha_voltage_0)*0.5
#     gamma_voltage = (gamma_solution[0]*180/np.pi - gamma_voltage_0)*0.5

#     return (alpha_voltage, gamma_voltage)

class PositionTracker:
    def __init__(self, distance, redpitaya_object):
        self.x = 0
        self.y = 0
        self.distance = distance
        self.voltages = (0, 0)
        self.mode_test = False
        self.rp = redpitaya_object

        ## fixed variables
        self.voltage_max = 1.8
        self.voltage_min = 0.0
        self.alpha_angle_0 = 45
        self.gamma_angle_0 = 40
        ### Calculate the initial y_value given initial gamma angle
        self.y_offset = z_equation(self.gamma_angle_0*np.pi/180, self.distance, 0)
        

    def print_position(self):
        print("Current position: x =", self.x, "y =", self.y)

    def solve_voltage(self, msg = True):
        ## scipy solver works best with initial guess of pi/4
        initial_guess = np.pi/4
        ## Incase we need to set a target offset create a new target object (Legacy)
        target = (self.x, self.y + self.y_offset)


        ## Solve the equation numerically
        gamma_solution = fsolve(z_equation, initial_guess, args=(self.distance, target[1]))
        alpha_solution = fsolve(y_equation, initial_guess, args=(gamma_solution, self.distance, target[0]))

        ## Convert to voltage
        alpha_voltage = round((alpha_solution[0]*180/np.pi - self.alpha_angle_0)*0.5, 5)
        gamma_voltage = round((gamma_solution[0]*180/np.pi - self.gamma_angle_0)*0.5, 5)
        
        range_check = False
        ### Check if the voltage is within the range, if any are flag with range_check to handle correct location
        if alpha_voltage > self.voltage_max:
            range_check = True
            alpha_voltage = self.voltage_max
        elif alpha_voltage < self.voltage_min:
            range_check = True
            alpha_voltage = self.voltage_min
        if gamma_voltage > self.voltage_max:
            range_check = True
            gamma_voltage = self.voltage_max
        elif gamma_voltage < self.voltage_min:
            range_check = True
            gamma_voltage = self.voltage_min

        ### Set the voltages
        self.voltages = (alpha_voltage, gamma_voltage)
        ### Check range_check
        if range_check:
            if msg:
                print("Target location out of range, setting to closest location")
            ## set location
            self.get_location(msg=False)

        if msg:
            print("Voltage: alpha =", self.voltages[0], "gamma =", self.voltages[1])
        
        return self.voltages
    
    def get_location(self, msg = True):
        alpha_angle = self.alpha_angle_0 + self.voltages[0]*2
        gamma_angle = self.gamma_angle_0 + self.voltages[1]*2
        ### Call equations with arguments y_value and z_value set to 0 to get location given current voltages
        self.y = round(z_equation(gamma_angle*np.pi/180, self.distance, 0) - self.y_offset,3) 
        self.x = round(y_equation(alpha_angle*np.pi/180, gamma_angle*np.pi/180, self.distance, 0),3)
        if msg:
            print("Current position: x =", self.x, "y =", self.y)
        return (self.x, self.y)

    def set_voltage(self, msg = True):
        self.solve_voltage(msg)
        if self.mode_test:
            return
        ### Set AO0 to X-axis mirror voltage (pin 17)
        self.rp.set_voltage(0, self.voltages[0])
        ### Set AO2 to Y-axis mirror voltage (pin 19)
        self.rp.set_voltage(2, self.voltages[1])

    def get_bounding_box(self):
        self.reset_coordinates()
        voltage_range = np.linspace(self.voltage_min, self.voltage_max, 100)
        x_values = []
        y_values = []
        for i in range(100):
            gamma_voltage = voltage_range[i]
            self.voltages = (0, gamma_voltage)
            y_values.append(self.get_location(msg=False)[1])
            x_values_temp = []
            for j in range(100):
                alpha_voltage = voltage_range[j]
                self.voltages = (alpha_voltage, gamma_voltage)
                x_values_temp.append(self.get_location(msg=False)[0])
            # take max x value
            x_values.append(max(x_values_temp))
        ### The box is bounded by max y value, and smallest max x value
        x_limit = min(x_values)
        y_limit = max(y_values)
        return (x_limit, y_limit)
    


    def process_coordinates(self, x, y, msg = True):
        self.x = x
        self.y = y
        self.set_voltage(msg)

    ### use to reset coordinates to 0 without interfacing with red pitaya
    def reset_coordinates(self):
        self.x = 0
        self.y = 0
        self.solve_voltage()

    def clear_coordinates(self):
        self.x = 0
        self.y = 0
        self.set_voltage()