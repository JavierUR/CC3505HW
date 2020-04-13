# coding=utf-8
"""
Javier Urrutia, CC3501, 2020-1
Utilities for the game
"""
import numpy as np

def checkHitbox(x, y, x1, y1, x2, y2):
    # Determine if point is inside hitbox
    return (x1 < x < x2) and (y2 < y < y1)
    
# A class to ahndle trayectories
class Trayectory:
    def __init__(self, ti, dt):
        self.ti = ti
        self.dt = dt

    def normalize_time(self, time):
        localTime = (time - self.ti) / self.dt
        return np.clip(localTime, 0, 1)

# Class for linear trayectories
class LinearTrayectory(Trayectory):
    
    def __init__(self, ti, dt, x1, y1, x2, y2):
        super().__init__(ti, dt)
        self.p1 = np.array([x1, y1])
        p2 = np.array([x2, y2])
        self.vect = p2 - self.p1

    def get_pos(self, time):
        t = self.normalize_time(time)
        return self.p1 + t*self.vect
