# coding=utf-8
"""
Javier Urrutia, CC3501, 2020-1
Utilities for the game
"""
import numpy as np

def checkHitbox(x, y, x1, y1, x2, y2):
    # Determine if point is inside hitbox
    return (x1 < x < x2) and (y2 < y < y1)
    
def derangement(n):
    # index array with all elements shuffled
    if n ==1: 
        return [0]
    v=np.arange(n)
    num=v.copy()
    while True:
        np.random.shuffle(v)
        if np.all((v-num)!=0):
            break
    return v

# A class to handle trayectories
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
