# coding=utf-8
"""
Javier Urrutia, CC3501, 2020-1
Space Wars game, designe with the 
model of the game
"""
import numpy as np

import transformations as tr
import scene_graph as sg

import game_shapes as gs
# A class to manage a shot movement
class Shot(object):
    speed = 0.9
    def __init__(self, x, y):
        self.currentX = x
        self.currentY = y
        self.inScreen = True

class PlayerShot(Shot):
    def __init__(self, x, y):
        super().__init__(x, y)

    def updatePos(self, dt):
        self.currentY += dt*self.speed
        self.inScreen = (self.currentY < 1.0)

class EnemyShot(Shot):
    def __init__(self, x, y):
        super().__init__(x, y)

    def updatePos(self, dt):
        self.currentY -= dt*self.speed
        self.inScreen = (self.currentY > -1.0)

# A class to manage each enemy
class Enemy:
    def __init__(self, x, y, time):
        self.currentX = x
        self.currentY = y
        self.alive = True
        self.initTime = time
        self.lastShoot = time

    def spawnShoot(self):
        return EnemyShot(self.currentX, self.currentY - 0.1)

    def shouldShoot(self, time):
        if (time - self.lastShoot) >2:
            self.lastShoot = time
            return True
        else:
            return False
        
def checkHitbox(x,y, x1,y1, x2,y2):
    # Determine if point is inside hitbox
    return (x > x1 and x < x2) and (y < y1 and y > y2)

# A class to manage game state
class GameModel:
    def __init__(self, enemies, screenWidht, screenHeight, controller):
        # Start clock
        self.ltime = 0.0
        # reference to the game controller
        self.controller = controller
        # Create game scene
        self.gameScene = sg.SceneGraphNode("gameScene")
        self.gameScene.transform = tr.scale(screenHeight/screenWidht,1.0,1.0)

        # Load game models
        self.enemyModel = gs.createEnemy()
        self.playerModel = gs.createPlayer()
        self.playerShotModel = gs.createShot(0.9,0.5,0.0)
        self.enemyShotModel = gs.createShot(0.4,0.2,1.0)

        # Spawn player
        self.playerX = 0.0
        self.playerY = -0.75
        self.player = sg.SceneGraphNode("Player")
        self.player.transform = tr.translate(self.playerX, self.playerY, 0.0)
        self.player.childs = [self.playerModel]

        self.playerSpeed = 1.0
        self.playerLSTime = 0.0
        self.playerFR = 0.8

        # Objects list
        self.playerShots = []
        self.enemyShots = []
        self.enemies = []

        # Game status
        self.gameover = False

        self.enemies.append(Enemy(0, 0, 0.0))
        self.enemies.append(Enemy(0.2, 0, 0.5))

    def movePlayer(self, dt):
        # Change speed if moving in two axes
        if (self.controller.right or self.controller.left) and \
                (self.controller.up or self.controller.down):
            vp = self.playerSpeed / np.sqrt(2)
        else:
            vp = self.playerSpeed
        self.playerX += dt*vp*(self.controller.right - self.controller.left )
        self.playerY += dt*vp*(self.controller.up - self.controller.down )
        # Avoid leaving the screen
        self.playerX = np.clip(self.playerX,-0.7,0.7)
        self.playerY = np.clip(self.playerY,-0.9,0.8)

    def spawnPlayerShot(self):
        self.playerShots.append(PlayerShot(self.playerX,self.playerY+0.1))

    def checkEnemyHit(self, shot):
        for enemy in self.enemies:
            if checkHitbox(shot.currentX, shot.currentY, 
                    enemy.currentX-0.08, enemy.currentY+0.05,
                    enemy.currentX+0.08, enemy.currentY-0.05):
                enemy.alive = False
                return True
        return False

    def checkPlayerHit(self, shot):
        if checkHitbox(shot.currentX, shot.currentY, 
                self.playerX-0.08, self.playerY+0.05,
                self.playerX+0.08, self.playerY-0.05):
            self.gameover = True
            print("DEAD")
            return True
        return False

    def moveShots(self, dt):
        currentPlayerShots = []
        currentEnemyShots = []
        graphicShots = []
        for i,pshot in enumerate(self.playerShots):
            if pshot.inScreen:
                if not self.checkEnemyHit(pshot):
                    pshot.updatePos(dt)
                    shot = sg.SceneGraphNode(f"PShot_{i}")
                    shot.transform = tr.translate(pshot.currentX,pshot.currentY,0.0)
                    shot.childs = [self.playerShotModel]
                    graphicShots.append(shot)
                    currentPlayerShots.append(pshot)
        self.playerShots = currentPlayerShots
        for i,eshot in enumerate(self.enemyShots):
            if eshot.inScreen:
                if not self.checkPlayerHit(eshot):
                    eshot.updatePos(dt)
                    shot = sg.SceneGraphNode(f"EShot_{i}")
                    shot.transform = tr.translate(eshot.currentX,eshot.currentY,0.0)
                    shot.childs = [self.enemyShotModel]
                    graphicShots.append(shot)
                    currentEnemyShots.append(eshot)
        self.enemyShots = currentEnemyShots
        return graphicShots

    def manageEnemies(self, time, dt):
        screenEnemies = []
        for i,enemy in enumerate(self.enemies):
            if enemy.alive:
                # spawn enemy shoot
                if enemy.shouldShoot(time):
                    self.enemyShots.append(enemy.spawnShoot())
                screenEnemy = sg.SceneGraphNode(f"enemy_{i}")
                screenEnemy.transform = tr.translate(enemy.currentX,enemy.currentY,0.0)
                screenEnemy.childs = [self.enemyModel]
                screenEnemies.append(screenEnemy)
        return screenEnemies

    def updateScene(self, time):
        dt = time - self.ltime
        self.ltime = time
        # Update player position
        self.movePlayer(dt)
        self.player.transform = tr.translate(self.playerX, self.playerY, 0.0)
        # manage shots
        if self.controller.fire and (time - self.playerLSTime)>self.playerFR:
            self.spawnPlayerShot()
            self.playerLSTime = time

        screenShots = self.moveShots(dt)

        screenEnemies = self.manageEnemies(time, dt)

        self.gameScene.childs = [self.player]+screenShots+ screenEnemies
        #print(sg.findPosition(player,"Player"))
        return self.gameScene