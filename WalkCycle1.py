import time
import math
import board
import busio
from adafruit_pca9685 import PCA9685

# --- Constants ---
SERVO_FREQ = 50  # Hz

LENGTH_A = 10
LENGTH_B = 11.5

# Pulse width range in milliseconds (adjust per servo if needed)
MIN_PULSE_MS = 0.5
MAX_PULSE_MS = 2.5

# --- I2C Setup ---
i2c = busio.I2C(board.SCL, board.SDA)
pwm = PCA9685(i2c)
pwm.frequency = SERVO_FREQ

def ik(target_x, target_y):
    X1, Y1 = 0.0, 0.0
    X2, Y2 = target_x, target_y

    a = LENGTH_A
    b = LENGTH_B

    c = math.sqrt((X1 - X2)**2 + (Y1 - Y2)**2)
    if c == 0:
        return

    phi1rad = -math.acos((a**2 + c**2 - b**2) / (2 * a * c))
    phi2rad = math.acos((a**2 + b**2 - c**2) / (2 * a * b))

    dx = X2 - X1
    dy = Y2 - Y1
    angleR = math.atan2(dy, dx)

    X3 = X1 + a * math.cos(angleR + phi1rad)
    Y3 = Y1 + a * math.sin(angleR + phi1rad)
    servoAngleTop = -math.atan((X1 - X3) / (Y1 - Y3)) * 180 / math.pi + 90
    servoAngleBottom = -math.atan((X2 - X3) / (Y2 - Y3)) * 180 / math.pi + 90

    angle_set = [servoAngleTop, servoAngleBottom]
    return angle_set

def list_angles_from_points(points):
    angle_pairs = []
    for point in points:
        pair = ik(point[0], point[1])
        angle_pairs.append(pair)
    return angle_pairs

def set_servo_angle(channel, angle):
    # Clamp angle
    angle = max(0, min(180, angle))

    # Convert angle → pulse width (ms)
    pulse_ms = MIN_PULSE_MS + (angle / 180.0) * (MAX_PULSE_MS - MIN_PULSE_MS)

    # Convert to duty cycle
    period_ms = 1000.0 / SERVO_FREQ
    duty_cycle = int((pulse_ms / period_ms) * 65535)

    pwm.channels[channel].duty_cycle = duty_cycle

def disable_all_servos():
    for ch in range(16):
        pwm.channels[ch].duty_cycle = 0

def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# --- Leg Class ---
class Leg:
    def __init__(self, top_channel, bottom_channel, hip_channel):
        self.top_channel = top_channel
        self.bottom_channel = bottom_channel
        self.hip_channel = hip_channel

	# calculates angles to reach a taraget point and sets servos to those angles to reach it
    def point(self, target_x, target_y):
        angles = ik(target_x, target_y)
        angleTop = angles[0]
        angleBottom = angles[1]
        set_servo_angle(self.top_channel, angleTop)
        set_servo_angle(self.bottom_channel, angleBottom)

	# takes two already determined angles and just sets the servos to them
    def set_angles(self, angleTop, angleBottom, angleHip):
            set_servo_angle(self.top_channel, angleTop)
            set_servo_angle(self.bottom_channel, angleBottom)
            set_servo_angle(self.hip_channel, angleHip)

# --- Walking Gait Functions ---
def gait1(leg1_list, leg2_list): # two lists of angles must have same number of points
    if len(leg1_list) != len(leg2_list):
        print("gait1 failed because paths have different number of points")
    else:
        for angle_pair in range(len(leg1_list)): # for each set of angles in the gait, set a legs to the angle for that point.
                                                 # when setting a LEFT leg, swap 0 & 180 by mapping the value in 0-180 to 180-0.
            FR_leg.set_angles(leg1_list[angle_pair][0], leg1_list[angle_pair][1], 90)
            BL_leg.set_angles(map_value(leg1_list[angle_pair][0], 0.0, 180.0, 180.0, 0.0), map_value(leg1_list[angle_pair][1], 0.0, 180.0, 180.0, 0.0), 90)

            FL_leg.set_angles(map_value(leg2_list[angle_pair][0], 0.0, 180.0, 180.0, 0.0), map_value(leg2_list[angle_pair][1], 0.0, 180.0, 180.0, 0.0), 90)
            BR_leg.set_angles(leg2_list[angle_pair][0], leg2_list[angle_pair][1], 90)

            time.sleep(0.025)

def interpolate(val1, val2, steps=10):
    interpolated_vals = []
    for i in range(1, steps):
        t = i/steps
        val = val1+t*(val2-val1)
        interpolated_vals.append(val)
    interpolated_vals.append(val2)
    return interpolated_vals

def interpolate_angle_list(angle_sets, steps=10):
    new_sets_of_angles = []
    print("func called")
    for s in range(steps*len(angle_sets)): #Creating the 15 blank sets. Runs 15 times
        new_sets_of_angles.append([])
    for set in range(len(angle_sets)): #Looks at pair of angles in the 3 sets of angles list. Runs 3 times
        print(f"set loop. {set+1}/{len(angle_sets)}")
        print(f"{new_sets_of_angles}")
        for angle in range(len(angle_sets[set])): # Looks at first angle in first pair and first angle in second pair
            print(f"angle loop. {angle+1}/{len(angle_sets[set])}")
            intd_angles = interpolate(angle_sets[set][angle], angle_sets[(set+1)%len(angle_sets)][angle], steps)
            for a in range(len(intd_angles)): #Takes new set of 5 angles and puts them in the new_sets_of_angles list 
                new_sets_of_angles[a+((set-1)*steps)].append(intd_angles[a])
    return new_sets_of_angles

# --- Create Leg Instances ---
FR_leg = Leg(8, 9, 10)
BR_leg = Leg(4, 5, 6)
FL_leg = Leg(12, 13, 14)
BL_leg = Leg(0, 1, 2)


# --- Main Program Code ---
try:
    point_list_1 = [[-8,-17],[-4,-14],[-1,-12],[1,-17]]
    angle_list_1 = list_angles_from_points(point_list_1)
    interpolated_list_1 = interpolate_angle_list(angle_list_1,10)

    point_list_2 = [[-1,-12],[1,-17],[-8,-17],[-4,-14]]
    angle_list_2 = list_angles_from_points(point_list_2)
    interpolated_list_2 = interpolate_angle_list(angle_list_2,10)

    #angle_list_test = [[0,180],[90,90],[180,0]]
    #interpolated_list_test = interpolate_angle_list(angle_list_test,5)

    #print(f"{interpolated_list_test}")
    print(f"{interpolated_list_1}\n\n{interpolated_list_2}")
    while True:
        gait1(interpolated_list_1, interpolated_list_2)

except KeyboardInterrupt:
    print("\nStopping... disabling servos")
    disable_all_servos()
    pwm.deinit()

