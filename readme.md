Author: Daniel Perry
Date: Summer 2023

# Overview
- Aim: Develop a replacement for a Laser Doppler Velocimeter scanner that will be capable of faster scanning, as well as alternative types of laser scans 
- Equipment:
	- Polytec Vibrometer Controller (OFV 3001 S)
	- Polytec Sensor Head (OFV 303)
	- Thorlabs Galvo System (GVSO12/M)
	- Red Pitaya controller
	- Frequency generator (speaker)

# Set up and go
## Wiring and Physical components
Note: Refer to the documentation for individual components
- Galvo Mirrors:
	- Each Mirror has an associated driver board. The driver boards need to be connected to the galvo drive (Connection J9) and the power supply (Connection J10). For control, the positive pin on Connection J7 needs to be wired to a slow analog output pin on the Red Pitaya, and the negative and ground pins can both be wired to the Red Pitaya's grounding pin. 
	- My code assumes that the X-axis mirror is wired to pin 17 (Analog out 0) and the Y-axis mirror is wired to pin 19 (Analog out 1) on the Red Pitaya.
- Laser Vibrometer:
	- The laser head is connected to the controller with a Sub-D cable. 
	- My code assumes that the "Velocity Output" is connected to "Fast Analog Input 1" on the Red Pitaya
	- The laser provides reasonable reading when correctly focused, this can be achieved manually with the focus ring or through the controller
	- With the objects I measured good results were obtained with the controller set to 125 mm/s/V and a velocity filter of around 50kHz
- Signal Generator (Generic):
	- My code assumes that the Signal Generator is connected to "Fast Analog Output 1" on the Red Pitaya
	- The reference signal should be looped back to the Red Pitaya, in my case connected to "Fast Analog Input 2"
- Red Pitaya:
	- Connect the Red Pitaya to your laptop via ethernet cable
	- Note the mac address (6 digit alphanumeric) to navigate to the web interface at `http://rp-XXXXXX.local` (mac address in place of X's)
	- Turn on the SCPI server and note the local IP address

## Scanning an object
- Set up
	- Prepare the Red Pitaya
	- Prior to running `main.py`, set the variables for the object distance and red pitaya IP
	- Ensure the Red Pitaya's SCPI server is running then run `main.py`
- Scanning
	- The interface is simple, the canvas represents the scanning area of the laser and the laser will move to the location selected by the mouse
	- To set the coordinates of the object to be scanned click through the "set: XXXX " button. The first time its selected it will set the top left corner, than continue clockwise until 4 corners are set
	- When all vertices are defined select the button once more and the scanning area will be set to the largest rectangle that fits within the vertices
	- The configuration can be saved/loaded by selecting "save current configuration" or "load saved configuration" and entering a file name in the terminal 
	- Selecting "scan object" will begin scanning all points in the scanning area. It is configured to scan every mm. When scanning is complete enter a file name in the terminal to save the scan data to the subdirectory `sampledata/experiments/`


# How it works
## System
- Red Pitaya controls the reference frequency generation,  laser location (through mirror control), and reading the laser vibrometer response 
	-   The Red Pitaya is capable of generating and receiving 'fast' analog signals making it suitable to both test a full range of reference signals and read the vibrometer response
- The Galvo System consists of two rotating mirrors, and laser location controlled based on computed inverse kinematic functions
- A simple GUI was created in python to test and validate the system

## Python
- Red Pitaya provides limited documentation however their [SCPI support](https://redpitaya.readthedocs.io/en/latest/appsFeatures/remoteControl/remoteControl.html#list-of-supported-scpi-commands) is largely comprehensive. (Note that the [redpitaya_scpi.py](https://github.com/RedPitaya/RedPitaya/blob/master/Examples/python/redpitaya_scpi.py) is used to support the connection)
- My code is built with a Tkinter GUI on top of a set of classes used to interface with the Red Pitaya
- Its important to understand the desired functionality as well as the quirks involved with interfacing with the Red Pitaya

### Red Pitaya
Interfacing with the Red Pitaya involves some idiosyncrasies, below is a quick overview
- Inconsistencies with the triggering functions, the current data acquisition loop works by
	1. Prepare a single burst wave/impulse
	2. Start acquisition and trigger now
	3. Turn on the output and then trigger immediately
	4. Enter a while loop until the Red Pitaya returns a triggered message
	5. Sleep for a duration greater than the buffer length (buffer length calculated as $\frac{\text{decimation}}{\text{sampling rate}=125\times10^6} \times \text{buffer size}=16384$)
	6. Call to read buffer data on both inputs twice (unsure why but calling twice avoided some erroring)

### Mirror Control
- See appendix for overview of math involved, but that process provided equations for the Y and Z coordinates of the laser given the distance to the object and the angles of each mirror. (in code note that occasionally the coordinate system changes to Y->X and Z->Y I apologise for the inconsistency)
- The Z value depends only on the Y-axis mirror, while the Y value depends on both the Y and Z axis mirrors
- Using `scipy.optimize.fsolve` the required Y-axis mirror angle can be computed for a given Z coordinate, and then the required X-axis mirror angle can be computed given both the required Y-axis angle and Y coordinate.
- Out of the box the Red Pitaya provides voltages ranging from 0-1.8 giving 3.6 degrees of motion to each mirror, however the galvo system can support up to 15 degrees of motion. 
	- This means that if an object is too large to be scanned in the existing set-up, the mirror system can either be moved further away or the voltage inputs can be stepped up to offer a wider range of scanning angles



### Data Acquisition
- Sending reference wave
	- Sending a single burst wave after starting the data acquisition offered the fastest performance and data was cleaned in a post processing step
- Reading response data
	- The Red Pitaya occasionally failed to return the correct data unless the `self.rp_s.tx_txt('ACQ:SOUR1:DATA?')` command was sent twice (for each data input)
- Simple data processing heuristics
	- Quick checks for valid data are implemented in the acquisition loop to check for obvious data issues (largely due to focus issues with the laser controller)
- Data class
	- A data class was implemented to handle data processing but performance could be improved. Currently all data will be saved in memory until the scan is complete when it will be saved as a pandas pickle object

### Overall Control loops
1. User sets object outline from GUI
2. Determine a rectangular scan area, create a set of points to scan
3. Iterate through scanning points, at each point:
	1. Laser acquisition loop (include details)
	2. Check if data is valid, if not return to laser acquisition loop
	3. Move to next point


## Appendix

### Mirror Math

#### Concepts
Three basic concepts:
1. Law of Reflection (vector and matrix forms):
	- For a reflective surface with normal vector $\hat{n}$ and an incident beam $\hat{k}_1$ the reflected beam $\hat{k}_2$ is given by: $$\hat{k}_2 = \hat{k}_1 - 2(\hat{k}_1 \cdot \hat{n})\hat{n}$$
	- With the matrix $M = I-2\hat{n} \cdot \hat{n}^T$ we can express the law of reflection as: $$ \hat{k}_2 = M\hat{k}_1$$
	- Sequential reflections $M_1, M_2, ...$ can be 'chained together' so  $\hat{k}_2 = M_1M_2 \hat{k}_1$
1. Rotational transformation matrices:
	- The galvo system is composed of 2 rotating mirrors, in order to express their normal vectors as a function of their rotation we use the rotational transformation matrices (shown below for the typical cartesian coordinates):
$$
\begin{align*} \begin{array}{ccc} \text{x-axis rotation:} & \begin{bmatrix} 1 & 0 & 0 \\ 0 & \cos(\alpha) & -\sin(\alpha) \\ 0 & \sin(\alpha) & \cos(\alpha) \end{bmatrix} \\ \text{y-axis rotation:} & \begin{bmatrix} \cos(\beta) & 0 & \sin(\beta) \\ 0 & 1 & 0 \\ -\sin(\beta) & 0 & \cos(\beta) \end{bmatrix} \\ \text{z-axis rotation:} & \begin{bmatrix} \cos(\gamma) & -\sin(\gamma) & 0 \\ \sin(\gamma) & \cos(\gamma) & 0 \\ 0 & 0 & 1 \end{bmatrix} \end{array} \end{align*}
$$
3. Intersection of a beam and a plane:
	- For a vector $\hat{k} = \begin{pmatrix} a  \\ b  \\ c  \end{pmatrix}$ with an origin $\begin{pmatrix} x_b  \\ y_b  \\ z_b  \end{pmatrix}$ we can express a beam as $$\text{beam: }\begin{pmatrix} x  \\ y  \\ z  \end{pmatrix} = \hat{k}t + \begin{pmatrix} x_0  \\ y_0  \\ z_0  \end{pmatrix}$$
	- For a normal vector $\hat{n}$ and point on the plane  $p_0 = \begin{pmatrix} x_p  \\ y_b  \\ c_b  \end{pmatrix}$ the set of points $p$ which define the plane can be expressed as $$\text{plane: }\text{plane: }(p-p_0)\cdot \hat{n} = 0$
	- Substituting $p$ for the expression of the beam we can solve for the parameter $t$: $$
	\begin{align*} 
	\Big(\begin{pmatrix} x  \\ y  \\ z  \end{pmatrix}-\begin{pmatrix} x_p  \\ y_p  \\ z_p  \end{pmatrix}\Big)\cdot \hat{n} &= 0 \\
	\Big(\hat{k}t + \begin{pmatrix} x_b  \\ y_b  \\ z_b  \end{pmatrix} - \begin{pmatrix} x_p  \\ y_p  \\ z_p  \end{pmatrix} \Big)\cdot \hat{n} &= 0  \\
	\hat{k}t\cdot\hat{n} + \begin{pmatrix} x_b - x_p  \\ y_b - y_p  \\ z_b - z_p  \end{pmatrix}\cdot \hat{n} &= 0 \\
	t &= \frac{\begin{pmatrix} x_p - x_b  \\ y_p - y_b  \\ z_p - z_b  \end{pmatrix}\cdot\hat{n}}{\hat{k}\cdot\hat{n}}
	
	\end{align*}$$
	- The point of intersection can then be solved by substituting the value of $t$ back into the equation of the beam


#### Setting up the problem
First I want to apologise if the coordinate system seems inconsistent, but for all mirror math I defined the y-axis as the axis of the incident beam, the x-axis as the axis towards the target object (in other words roughly the reflective beam) and the z-axis simply as an upwards vertical axis. 
![[galvo_coordinates.png]]

- A detail to keep in mind is that the two mirrors are not orthogonal to each other. I chose to model the Y-axis mirror along a single Y-axis, while the X-axis mirror rotates around the X and Z axiis (however it is still referred to as the X-axis mirror). 
- I defined the rotation angle of the X-axis mirror with the angle $\alpha$ and the rotation angle of the Y-axis mirror with the angle $\beta$ 
- In initial modelling I assumed that incident beam $\hat{k}_1$ was perfectly along the Y-axis
directed at the centre of the X-axis mirror which I defined as point (0,0,0) and that the target object was located distance $d$ along the X-axis with a normal vector only in the X-axis
	 - Notation: $\hat{k}_1 = \begin{pmatrix} 0  \\ -1  \\ 0  \end{pmatrix}$; $\hat{n}_{object} = \begin{pmatrix} -1  \\ 0  \\ 0  \end{pmatrix}$ 
 - From the CAD files [provided by thorlabs](https://www.thorlabs.com/thorProduct.cfm?partNumber=GVS012) I found that the angle between the X-axis mirror and the Z-axis (in other words the fixed Y-axis rotation) was $10.454^{\circ}$ and that the center of the Y-axis mirror was -3.825 mm in the X-Axis, -0.504mm in the Y-axis and 15.705mm in the Z-axis apart from the centre of the X-axis mirror


*The underlying objective is to be able to control and direct the beam to an arbitrary point on the surface, in other words given a $(d,y,z)$ with $d$ the distance to the object and $y,z$ our point  what is the required  $\alpha$ and $\beta$.*

#### Reflection Matrices
Aim: Express the reflection matrices for each mirror $M_1, M_2$ (expressed as a function of normal vectors $\hat{n}_1, \hat{n}_2$) as functions of $\alpha$ and $\beta$.

- X-axis mirror normal vector: (solve for normal vector relative to only the mirror $\hat{n}_1^\star$, then translate to the global frame by the mirrors offset angle $\hat{n}_1$)
	- Define $\hat{n}_1^\star(\alpha=0):\begin{pmatrix} 0 \\ 0  \\ -1  \end{pmatrix}$ and $\hat{n}_1^\star(\alpha=90):\begin{pmatrix} 0 \\ -1  \\ 0  \end{pmatrix}$ we can use the x axis transformation matrix to obtain $\hat{n}_1^\star(\alpha):\begin{pmatrix} 0 \\ -sin(\alpha)  \\ -cos(\alpha)  \end{pmatrix}$ and applying the Y-axis rotation for $\theta = 10.454$ to get: $$\hat{n}_1(\alpha):\begin{pmatrix} -sin(\theta)cos(\alpha) \\ -sin(\theta)  \\ -cos(\theta)cos(\alpha)  \end{pmatrix}$$
- Y-axis mirror normal vector: 
	- Define $\hat{n}_2(\gamma=0):\begin{pmatrix} 0 \\ 0  \\ 1  \end{pmatrix}$ and $\hat{n}_2(\gamma=90):\begin{pmatrix} -1 \\ 0  \\ 0  \end{pmatrix}$ we can use the y-axis transformation matrix to obtain normal vector $\hat{n}_2$ and reflection matrix $M_2$ $$
\hat{n}_2(\gamma):\begin{pmatrix} -sin(\gamma) \\ 0  \\ cos(\gamma)  \end{pmatrix}$$
- Reflection matrices:
	- Using $M = I-2\hat{n} \cdot \hat{n}^T$ and that sequential transformation matrices can be expressed as $M_3 = M_2 M_1$ the full reflection matrix can be expressed as (skipping intermediary steps):
$$
\left[\begin{matrix}\frac{\cos{\left(2 \gamma \right)}}{2} - \frac{\cos{\left(2 \alpha - 2 \gamma \right)}}{4} - \frac{\cos{\left(2 \alpha + 2 \gamma \right)}}{4} + \frac{\cos{\left(2 \gamma + 2 \theta \right)}}{2} + \frac{\cos{\left(- 2 \alpha + 2 \gamma + 2 \theta \right)}}{4} + \frac{\cos{\left(2 \alpha + 2 \gamma + 2 \theta \right)}}{4} & - \frac{\cos{\left(- 2 \alpha + 2 \gamma + \theta \right)}}{2} + \frac{\cos{\left(2 \alpha + 2 \gamma + \theta \right)}}{2} & \frac{\sin{\left(2 \gamma \right)}}{2} + \frac{\sin{\left(2 \alpha - 2 \gamma \right)}}{4} - \frac{\sin{\left(2 \alpha + 2 \gamma \right)}}{4} - \frac{\sin{\left(2 \gamma + 2 \theta \right)}}{2} - \frac{\sin{\left(- 2 \alpha + 2 \gamma + 2 \theta \right)}}{4} - \frac{\sin{\left(2 \alpha + 2 \gamma + 2 \theta \right)}}{4}\\- \frac{\cos{\left(2 \alpha - \theta \right)}}{2} + \frac{\cos{\left(2 \alpha + \theta \right)}}{2} & \cos{\left(2 \alpha \right)} & - \frac{\sin{\left(2 \alpha - \theta \right)}}{2} - \frac{\sin{\left(2 \alpha + \theta \right)}}{2}\\- \left(2 \sin^{2}{\left(\theta \right)} \cos^{2}{\left(\alpha \right)} - 1\right) \sin{\left(2 \gamma \right)} + 2 \sin{\left(\theta \right)} \cos^{2}{\left(\alpha \right)} \cos{\left(2 \gamma \right)} \cos{\left(\theta \right)} & - \frac{\sin{\left(- 2 \alpha + 2 \gamma + \theta \right)}}{2} + \frac{\sin{\left(2 \alpha + 2 \gamma + \theta \right)}}{2} & \left(2 \cos^{2}{\left(\alpha \right)} \cos^{2}{\left(\theta \right)} - 1\right) \cos{\left(2 \gamma \right)} - 2 \sin{\left(2 \gamma \right)} \sin{\left(\theta \right)} \cos^{2}{\left(\alpha \right)} \cos{\left(\theta \right)}\end{matrix}\right]
$$


#### Computing the final beam location
The incident beam defined by $\hat{k}_1$ is reflected off of point $E_1$ on the X-axis mirror with direction $\hat{k}_2$ onto point $E_2$ on the Y-axis mirror where it is reflected in direction $\hat{k}_3$ towards the object arriving at point $E_3$. So the final location of the beam $E_3$ requires solving for both the final reflected vector $\hat{k}_3$ and the point $E_2$. Expressions for both $E_2$ and $E_3$ are with $x_2,y_2,z_2$ the offset values of the Y-axis mirror with respect to the X-axis mirror:

$$\begin{align*}
E_2 &=\left[\begin{matrix}- \frac{\left(x_{2} \sin{\left(\gamma \right)} - z_{2} \cos{\left(\gamma \right)}\right) \sin{\left(\theta \right)}}{\cos{\left(\gamma + \theta \right)}}\\\frac{2 \left(x_{2} \sin{\left(\gamma \right)} - z_{2} \cos{\left(\gamma \right)}\right) \cos{\left(2 \alpha \right)}}{- \sin{\left(- 2 \alpha + \gamma + \theta \right)} + \sin{\left(2 \alpha + \gamma + \theta \right)}}\\- \frac{\left(x_{2} \sin{\left(\gamma \right)} - z_{2} \cos{\left(\gamma \right)}\right) \cos{\left(\theta \right)}}{\cos{\left(\gamma + \theta \right)}}\end{matrix}\right]  \\
E_3 &= \left[\begin{matrix}d\\\frac{- 2 d \cos{\left(2 \alpha \right)} + 2 x_{2} \cos{\left(2 \alpha \right)} - x_{2} \cos{\left(2 \alpha - 2 \gamma \right)} - x_{2} \cos{\left(2 \alpha + 2 \gamma \right)} + z_{2} \sin{\left(2 \alpha - 2 \gamma \right)} - z_{2} \sin{\left(2 \alpha + 2 \gamma \right)}}{\cos{\left(- 2 \alpha + 2 \gamma + \theta \right)} - \cos{\left(2 \alpha + 2 \gamma + \theta \right)}}\\\frac{- d \cos{\left(\gamma \right)} - d \cos{\left(3 \gamma + 2 \theta \right)} - x_{2} \cos{\left(\gamma + 2 \theta \right)} + x_{2} \cos{\left(3 \gamma + 2 \theta \right)} + z_{2} \sin{\left(\gamma + 2 \theta \right)} + z_{2} \sin{\left(3 \gamma + 2 \theta \right)}}{\sin{\left(\gamma \right)} + \sin{\left(3 \gamma + 2 \theta \right)}}\end{matrix}\right]
\end{align*}
$$

#### Solving for a location
The Y and Z values of the target are given by the 2nd and 3rd rows of the $E_3$ matrix. Noting that the Z location depends only on the value of $\gamma$, root solving tools can be used to first solve the Z equation for $\gamma$ given a desired $z_3$. The required $\alpha$ can then be solved given $\gamma$ and $y_3$. 

Programatically, functions were first defined as:

```python
def z_equation(gamma, d, z_value):
	return (-d*np.cos(gamma) - d*np.cos(3*gamma + 0.368089939245604) + 15.705*np.sin(gamma + 0.368089939245604) + 15.705*np.sin(3*gamma + 0.368089939245604) + 3.825*np.cos(gamma + 0.368089939245604) - 3.825*np.cos(3*gamma + 0.368089939245604))/(np.sin(gamma) + np.sin(3*gamma + 0.368089939245604)) - z_value

def y_equation(alpha, gamma, d, y_value):
	return (-2*d*np.cos(2*alpha) + 15.705*np.sin(2*alpha - 2*gamma) - 15.705*np.sin(2*alpha + 2*gamma) - 7.65*np.cos(2*alpha) + 3.825*np.cos(2*alpha - 2*gamma) + 3.825*np.cos(2*alpha + 2*gamma))/(np.cos(-2*alpha + 2*gamma + 0.184044969622802) - np.cos(2*alpha + 2*gamma + 0.184044969622802)) - y_value
```

Then `scipy.optimize.fsolve` is used as a root finder:
```python
gamma_solution = fsolve(z_equation, initial_guess, args=(distance, target[1]))
alpha_solution = fsolve(y_equation, initial_guess, args=(gamma_solution, self.distance, target[0]))
```
