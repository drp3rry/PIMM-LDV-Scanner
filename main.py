import redpitaya_scpi as scpi

# from redpitaya.rphelper import rpwrapper
from redpitaya.lasercontrol import lasercontrol
import redpitaya.mirrorcontrol as mc

# rp = rpwrapper("169.254.29.96")
laser_controller = lasercontrol()
laser_controller.hello()
