# coding=utf-8
"""
Javier Urrutia, CC3501, 2020-1
Model of the game
"""
import numpy as np

import transformations as tr
import scene_graph as sg

import game_shapes as gs
import game_utils as gu

#Define ship states
S_ALIVE = 0
S_HIT   = 1
S_DEAD  = 2

#Define game states
G_ONGOING = 0
G_WIN   = 1
G_LOST  = 2

# A class to manage a shot movement
class Shot(object):
    speed = 0.9
    def __init__(self, x, y):
        self.currentX = x
        self.currentY = y
        self.inScreen = True

# Class for player shot
class PlayerShot(Shot):
    def __init__(self, x, y):
        super().__init__(x, y)

    def updatePos(self, dt):
        self.currentY += dt*self.speed
        self.inScreen = (self.currentY < 1.0)

# Class for enemy shot
class EnemyShot(Shot):
    def __init__(self, x, y):
        super().__init__(x, y)

    def updatePos(self, dt):
        self.currentY -= dt*self.speed
        self.inScreen = (self.currentY > -1.0)

# A class to manage game spaceships
class Ship:
    explosionTime = 0.2
    shipHalfWidth = 0.0
    shipHalfHeight = 0.0
    firePeriod = 1.0
    
    def __init__(self, name, x, y, createTime, visualModel, hp):
        self.currentX = x
        self.currentY = y
        self.sceneNode = sg.SceneGraphNode(name)
        self.sceneNode.transform = tr.translate(x, y, 0.0)
        self.sceneNode.childs = [visualModel]
        self.state = S_ALIVE
        self.lastShot = createTime
        self.deathTime = None
        self.hp = hp

    def manageHitState(self, time):
        # Function to manage ship explosion effect
        if (time-self.deathTime) > self.explosionTime:
            self.state = S_DEAD

    def takeHit(self, time):
        # Function to account hit
        self.hp -= 1
        if self.hp == 0:
            self.state = S_HIT
            self.deathTime = time

    def isHit(self, shot, time):
        # Function to verify if a shot hits the ship
        if self.state == S_ALIVE and \
                gu.checkHitbox(shot.currentX, shot.currentY,
                            self.currentX-self.shipHalfWidth, self.currentY+self.shipHalfHeight,
                            self.currentX+self.shipHalfWidth, self.currentY-self.shipHalfHeight):
            self.takeHit(time)
            return True
        return False

    def canShoot(self, time):
        # Funtion to verify if the fire period passed
        if (time - self.lastShot) > self.firePeriod:
            return True
        else:
            return False

# A class to manage each enemy
class Enemy(Ship):
    firePeriod = 2.0
    shipHalfWidth = 0.08
    shipHalfHeight = 0.04
    def __init__(self, name, x, y, time, trayectory, visualModel):
        super().__init__(name, x, y, time, visualModel, 1)
        self.trayectory = trayectory

    def spawnShot(self, time):
        # Spawn an enemy shot
        self.lastShot = time
        return EnemyShot(self.currentX, self.currentY - self.shipHalfHeight)


    def update(self,time):
        if self.state == S_ALIVE:
            # Update ship position
            self.currentX, self.currentY = self.trayectory.get_pos(time)
            self.sceneNode.transform = tr.translate(self.currentX, self.currentY, 0.0)
        elif self.state == S_HIT:
            self.manageHitState(time)

# A class to manage the player ship
class Player(Ship):
    firePeriod = 0.8
    shipHalfWidth = 0.08
    shipHalfHeight = 0.05
    playerSpeed = 1.0

    def __init__(self, name, x, y, time, controller, visualModel):
        super().__init__(name, x, y, time, visualModel, 3)
        self.controller = controller

    def spawnShot(self, time):
        # Spawn a player shot
        self.lastShot = time
        return PlayerShot(self.currentX, self.currentY + self.shipHalfHeight)

    def movePlayer(self, dt):
        # Change speed if moving in two axes
        if (self.controller.right or self.controller.left) and \
                (self.controller.up or self.controller.down):
            vp = self.playerSpeed / np.sqrt(2)
        else:
            vp = self.playerSpeed
        self.currentX += dt*vp*(self.controller.right - self.controller.left )
        self.currentY += dt*vp*(self.controller.up - self.controller.down )
        # Avoid leaving the screen
        self.currentX = np.clip(self.currentX,-0.7,0.7)
        self.currentY = np.clip(self.currentY,-0.9,0.4)

    def update(self, time, dt):
        if self.state == S_ALIVE:
            # Update player position
            self.movePlayer(dt)
            self.sceneNode.transform = tr.translate(self.currentX, self.currentY, 0.0)
        elif self.state == S_HIT:
            self.manageHitState(time)

# A class to manage game state
class GameModel:
    def __init__(self, nEnemies, screenWidht, screenHeight, controller):
        # Start clock
        self.ltime = 0.0
        # reference to the gaplayerme controller

        # Create game scene
        self.gameScene = sg.SceneGraphNode("gameScene")
        self.gameScene.transform = tr.scale(screenHeight/ screenWidht, 1.0, 1.0)

        # Load game models
        enemyModel = gs.create_enemy((0.5, 0, 0.38), (0.0, 0.38, 0.5))
        enemyModel2 = gs.create_enemy((0.73, 0.42, 0.34), (0.19, 0.28, 0.37))
        enemyModel3 = gs.create_enemy((0.03, 25, 0.47), (0.41, 0.45, 0.40))
        self.enemyModels = [enemyModel, enemyModel2, enemyModel3]
        self.playerModel = gs.create_player()
        self.playerShotModel = gs.create_shot(0.9, 0.5, 0.0)
        self.enemyShotModel = gs.create_shot(0.4, 0.2, 1.0)
        self.explosionmodel = gs.create_explosion()
        self.hpBlockModel = gs.create_hp_block()

        # Spawn player
        self.player = Player("player", 0.0, -0.75, self.ltime, controller, self.playerModel)

        # Objects list
        self.playerShots = []
        self.enemyShots = []
        self.enemies = []

        # Game status
        self.state = G_ONGOING
        self.remainingEnemies = nEnemies
        self.wave = 0
        self.lastEnemyTimer = 0.0 #time of last enemy death
        self.waitSpawn = False

    def checkEnemyHit(self, shot, time):
        # Function to check if a shot hits any enemy 
        for enemy in self.enemies:
            if enemy.isHit(shot, time):
                return True
        return False

    def moveShots(self, dt, time):
        # Function to move shots on the game and check hits
        currentPlayerShots = []
        currentEnemyShots = []
        for pshot in self.playerShots:
            if pshot.inScreen:
                if not self.checkEnemyHit(pshot, time):
                    pshot.updatePos(dt)
                    currentPlayerShots.append(pshot)
        self.playerShots = currentPlayerShots
        for eshot in self.enemyShots:
            if eshot.inScreen:
                if not self.player.isHit(eshot, time):
                    eshot.updatePos(dt)
                    currentEnemyShots.append(eshot)
        self.enemyShots = currentEnemyShots

    def spawnEnemies(self, time):
        #Wait 1 second before new enemies
        if not self.waitSpawn:
            self.lastEnemyTimer = time
            self.waitSpawn = True
        #Spawn new enemy wave
        elif self.remainingEnemies > 0 and (time-self.lastEnemyTimer) > 1.0:
            self.wave += 1
            toSpawn = min(np.clip(self.wave, 0, 5), self.remainingEnemies)
            x = np.arange(0, (toSpawn)*0.25, 0.25) - (toSpawn-1)*0.125
            x2 = x[gu.derangement(len(x))]
            waveModel = self.wave%3
            for i in range(toSpawn):
                trayectory = gu.LinearTrayectory(time, 1.5, x[i], 1.1, x2[i], 0.4)
                enemyShip = Enemy(f"enemy_{i}", x[i], 0.9, time + np.random.random(), 
                                    trayectory, self.enemyModels[waveModel])
                self.enemies.append(enemyShip)
                self.remainingEnemies -= 1
            self.waitSpawn = False

    def manageEnemies(self, time):
        # Function to update enemies status
        if len(self.enemies) == 0:
            if self.remainingEnemies == 0:
                self.state = G_WIN
            else:
                self.spawnEnemies(time)
        currentEnemies = []
        for i,enemy in enumerate(self.enemies):
            enemy.update(time)
            if enemy.state == S_ALIVE:
                # spawn enemy shoot
                if enemy.canShoot(time):
                    self.enemyShots.append(enemy.spawnShot(time))
            if enemy.state != S_DEAD:
                currentEnemies.append(enemy)
        self.enemies = currentEnemies

    def hpStatusDraw(self):
        # A bar displaying current player HP
        hpBar = sg.SceneGraphNode("hp_bar")
        hpBar.childs = []
        x = np.arange(0, (self.player.hp)*0.07, 0.07)
        for i in range(self.player.hp):
            hpBlock = sg.SceneGraphNode(f"hp_{i}")
            hpBlock.transform = tr.translate(x[i], 0.0, 0.0)
            hpBlock.childs = [self.hpBlockModel]
            hpBar.childs.append(hpBlock)
        hpStatus = sg.SceneGraphNode("hp_status")
        hpStatus.transform = tr.translate(-0.65, 0.9, 0.0)
        hpStatus.childs = [hpBar]
        return hpStatus

    def managePlayer(self, time, dt):
        # Manage the player ship
        # interaction
        self.player.update(time, dt)
        if self.player.state == S_ALIVE:
            # manage shots
            if self.player.controller.fire and self.player.canShoot(time):
                self.playerShots.append(self.player.spawnShot(time))
            # Player draw
        elif self.player.state == S_HIT:
            self.state = G_LOST

    def updateScene(self, time):
        dt = time - self.ltime
        self.ltime = time
        # Update game elements
        self.moveShots(dt, time)
        self.manageEnemies(time)
        self.managePlayer(time, dt)

    def getShipGraphNode(self, ship):
        # Function to get the scene node of a ship
        if ship.state == S_ALIVE:
            return ship.sceneNode
        elif ship.state == S_HIT:
            # If the ship is hit, draw an explosion
            explosion = sg.SceneGraphNode("dead_" + ship.sceneNode.name)
            explosion.transform = tr.translate(ship.currentX, ship.currentY, 0.0)
            explosion.childs = [self.explosionmodel]
            return explosion
        else:
            return None

    def getGameScene(self):
        screenElements = []
        for ship in [self.player]+self.enemies:
            node = self.getShipGraphNode(ship)
            if node is not None:
                screenElements.append(node)
        for i,eshot in enumerate(self.enemyShots):
            if eshot.inScreen:
                shot = sg.SceneGraphNode(f"EShot_{i}")
                shot.transform = tr.translate(eshot.currentX,eshot.currentY,0.0)
                shot.childs = [self.enemyShotModel]
                screenElements.append(shot)
        for i,pshot in enumerate(self.playerShots):
            if pshot.inScreen:
                shot = sg.SceneGraphNode(f"PShot_{i}")
                shot.transform = tr.translate(pshot.currentX,pshot.currentY,0.0)
                shot.childs = [self.playerShotModel]
                screenElements.append(shot)
        screenElements.append(self.hpStatusDraw())
        self.gameScene.childs = screenElements
        return self.gameScene
        
