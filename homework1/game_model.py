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

#Define ship states
S_ALIVE = 0
S_HIT   = 1
S_DEAD  = 2

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
        self.state = S_ALIVE
        self.initTime = time
        self.lastShot = time
        self.deathTime = None

    def spawnShot(self):
        return EnemyShot(self.currentX, self.currentY - 0.1)

    def shouldShoot(self, time):
        if (time - self.lastShot) >2:
            self.lastShot = time
            return True
        else:
            return False

    def update(self,time):
        if self.state == S_ALIVE:
            return
        elif self.state == S_HIT:
            if self.deathTime is None:
                self.deathTime = time
            elif (time-self.deathTime) > 0.2:
                self.state = S_DEAD
        
def checkHitbox(x,y, x1,y1, x2,y2):
    # Determine if point is inside hitbox
    return (x > x1 and x < x2) and (y < y1 and y > y2)

# A class to manage game state
class GameModel:
    def __init__(self, nEnemies, screenWidht, screenHeight, controller):
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
        self.explosionmodel = gs.createExplosion()

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
        self.remainingEnemies = nEnemies
        self.wave = 1
        self.lastEnemyTimer = 0.0 #time of last enemy death
        self.waitSpawn = False

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
            if enemy.state == S_ALIVE and checkHitbox(shot.currentX, shot.currentY, 
                                            enemy.currentX-0.08, enemy.currentY+0.05,
                                            enemy.currentX+0.08, enemy.currentY-0.05):
                enemy.state = S_HIT
                return True
        return False

    def checkPlayerHit(self, shot):
        if checkHitbox(shot.currentX, shot.currentY, 
                self.playerX-0.08, self.playerY+0.05,
                self.playerX+0.08, self.playerY-0.05):
            self.gameover = True
            return True
        return False

    def moveShots(self, dt):
        # Function to move shots on the game and check hits
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

    def spawnEnemies(self, time):
        #Wait 1 second before new enemies
        if not self.waitSpawn:
            self.lastEnemyTimer = time
            self.waitSpawn = True
        #Spawn new enemy wave
        elif self.remainingEnemies>0 and (time-self.lastEnemyTimer) > 1.0:
            self.enemies.append(Enemy(0.0,0.9,time))
            self.wave+=1
            self.remainingEnemies-=1
            self.waitSpawn = False

    def manageEnemies(self, time, dt):
        if len(self.enemies) == 0:
            self.spawnEnemies(time)
        screenEnemies = []
        currentEnemies = []
        for i,enemy in enumerate(self.enemies):
            enemy.update(time)
            if enemy.state==S_ALIVE:
                # spawn enemy shoot
                if enemy.shouldShoot(time):
                    self.enemyShots.append(enemy.spawnShot())
                screenEnemy = sg.SceneGraphNode(f"enemy_{i}")
                screenEnemy.transform = tr.translate(enemy.currentX,enemy.currentY,0.0)
                screenEnemy.childs = [self.enemyModel]
                screenEnemies.append(screenEnemy)
                currentEnemies.append(enemy)
            elif enemy.state==S_HIT:
                screenEnemy = sg.SceneGraphNode(f"dead_enemy_{i}")
                screenEnemy.transform = tr.translate(enemy.currentX,enemy.currentY,0.0)
                screenEnemy.childs = [self.explosionmodel]
                screenEnemies.append(screenEnemy)
                currentEnemies.append(enemy)
        self.enemies = currentEnemies
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