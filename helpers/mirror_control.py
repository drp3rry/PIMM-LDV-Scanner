import redpitaya_scpi as scpi
from scipy.optimize import fsolve
import numpy as np

IP = "169.254.29.96"
rp_s = scpi.scpi(IP)

def set_voltage(pin, voltage, print_voltage=False):
    rp_s.tx_txt('ANALOG:PIN AOUT'+str(pin)+',' + str(voltage))
    if print_voltage:
        print("Voltage setting for AO["+str(pin)+"] = "+str(voltage)+"V")

def y_equation(alpha, y, gamma, d):
    return (-2*d*np.cos(2*alpha) + 15.705*np.sin(2*alpha - 2*gamma) - 15.705*np.sin(2*alpha + 2*gamma) - 7.65*np.cos(2*alpha) + 3.825*np.cos(2*alpha - 2*gamma) + 3.825*np.cos(2*alpha + 2*gamma))/(np.cos(-2*alpha + 2*gamma + 0.184044969622802) - np.cos(2*alpha + 2*gamma + 0.184044969622802)) - y

def z_equation(gamma, d, z_value):
    return (-d*np.cos(gamma) - d*np.cos(3*gamma + 0.368089939245604) + 15.705*np.sin(gamma + 0.368089939245604) + 15.705*np.sin(3*gamma + 0.368089939245604) + 3.825*np.cos(gamma + 0.368089939245604) - 3.825*np.cos(3*gamma + 0.368089939245604))/(np.sin(gamma) + np.sin(3*gamma + 0.368089939245604)) - z_value


def mirror_solve(target, distance):
    # Initial guess for the solution
    initial_guess = np.pi/4
    # Correct for the z axis offset
    target = (target[0], target[1] + 27.5)

    # For conversion to voltage
    alpha_voltage_0 = 45
    gamma_voltage_0 = 40

    # Solve the equation numerically
    gamma_solution = fsolve(z_equation, initial_guess, args=(distance, target[1]))
    alpha_solution = fsolve(y_equation, initial_guess, args=(target[0], gamma_solution, distance))

    alpha_voltage = (alpha_solution[0]*180/np.pi - alpha_voltage_0)*0.5
    gamma_voltage = (gamma_solution[0]*180/np.pi - gamma_voltage_0)*0.5

    return (alpha_voltage, gamma_voltage)

class PositionTracker:
    def __init__(self, distance):
        self.x = 0
        self.y = 0
        self.distance = distance
        self.voltages = (0, 0)

    def print_position(self):
        print("Current position: x =", self.x, "y =", self.y)

    def solve_voltage(self):
        self.voltages =  mirror_solve((-self.x, self.y), self.distance)
        print("Voltage: alpha =", self.voltages[0], "gamma =", self.voltages[1])
        # return voltages
    
    def set_voltage(self):
        self.solve_voltage()
        set_voltage(0, self.voltages[0])
        set_voltage(2, self.voltages[1])