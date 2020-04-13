# coding=utf-8
"""
Javier Urrutia, CC3501, 2020-1
Utilities for the game
"""

def checkHitbox(x,y, x1,y1, x2,y2):
    # Determine if point is inside hitbox
    return (x > x1 and x < x2) and (y < y1 and y > y2)
    