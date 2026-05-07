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

# --- Create Leg Instances ---
FR_leg = Leg(8,9,10)
BR_leg = Leg(4,5,6)
FL_leg = Leg(12,13,14)
BL_leg = Leg(0,1,2)

# --- Main Loop ---
try:
    while True:
        FR_leg.set_angles(45, 135, 90)
        BR_leg.set_angles(45, 135, 90)
        FL_leg.set_angles(135, 45, 90)
        BL_leg.set_angles(135, 45, 90)
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping... disabling servos")
    #disable_all_servos()
    pwm.deinit()
