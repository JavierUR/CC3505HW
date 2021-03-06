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

# A class to manage each game element visual node
class GameElement:
    def __init__(self, name, x, y):
        # name - Name of the element
        # x - Start x position in game
        # y - Start y position in game
        self.currentX = x
        self.currentY = y
        self.sceneNode = sg.SceneGraphNode(name)
        self.sceneNode.transform = tr.translate(x, y, 0.0)

    def setVisual(self, visualModel):
        # Method to set the scene graph node model
        # visualModel - SceneGraphNode of the element visual model
        self.sceneNode.childs = [visualModel]

    def updateVisualPos(self):
        # Method to set visual node postion to element position
        self.sceneNode.transform = tr.translate(self.currentX, self.currentY, 0.0)
    
# A class to manage a shot movement
class Shot(GameElement):
    speed = 0.9
    def __init__(self, name, x, y):
        # name - Name of the shot
        # x - Start x position in game
        # y - Start y position in game
        super().__init__(name, x, y)
        self.inScreen = True

# Class for player shot
class PlayerShot(Shot):
    def __init__(self, x, y):
        # x - Start x position in game
        # y - Start y position in game
        super().__init__(f"pshot_{x}_{y}", x, y)

    def updatePos(self, dt):
        # Update shot position. Player shots move up
        # dt - Game frame time difference in seconds
        self.currentY += dt*self.speed
        self.updateVisualPos()
        self.inScreen = (self.currentY < 1.0)

# Class for enemy shot
class EnemyShot(Shot):
    def __init__(self, x, y):
        # x - Start x position in game
        # y - Start y position in game
        super().__init__(f"eshot_{x}_{y}", x, y)

    def updatePos(self, dt):
        # Update shot position. Enemy shots move down
        # dt - Game frame time difference in seconds
        self.currentY -= dt*self.speed
        self.updateVisualPos()
        self.inScreen = (self.currentY > -1.0)

# A class to manage game spaceships
class Ship(GameElement):
    explosionTime = 0.2
    shipHalfWidth = 0.0
    shipHalfHeight = 0.0
    firePeriod = 1.0
    
    def __init__(self, name, x, y, createTime, visualModel, hp):
        # name - Name of the ship
        # x - Start x position in game
        # y - Start y position in game
        # createTime - Ship creation time in seconds
        # visualModel - SceneGraphNode of the ship visual model
        # hp - Ship hitpoints
        super().__init__(name, x, y)
        self.setVisual(visualModel)
        #self.sceneNode.childs = [visualModel]
        self.state = S_ALIVE
        self.lastShot = createTime
        self.deathTime = None
        self.hp = hp

    def manageHitState(self, time):
        # Function to manage ship explosion effect
        # time - current clock time in seconds
        if self.state == S_HIT and (time-self.deathTime) > self.explosionTime:
            self.state = S_DEAD

    def takeHit(self, time):
        # Function to account hit
        self.hp -= 1
        if self.hp == 0:
            self.state = S_HIT
            self.deathTime = time

    def isHit(self, shot, time):
        # Function to verify if a shot hits the ship
        # shot - Shot object
        # time - current clock time in seconds
        if self.state == S_ALIVE and \
                gu.checkHitbox(shot.currentX, shot.currentY,
                            self.currentX-self.shipHalfWidth, self.currentY+self.shipHalfHeight,
                            self.currentX+self.shipHalfWidth, self.currentY-self.shipHalfHeight):
            self.takeHit(time)
            return True
        return False

    def canShoot(self, time):
        # Funtion to verify if the fire period passed
        # time - current clock time in seconds
        return (time - self.lastShot) > self.firePeriod

# A class to manage each enemy
class Enemy(Ship):
    firePeriod = 2.0
    shipHalfWidth = 0.08
    shipHalfHeight = 0.04
    orbitRadius = 0.1
    orbitSpeed = 1.5
    def __init__(self, name, x, y, time, trayectory, visualModel):
        # name - Name of the ship
        # x - Start x position in game
        # y - Start y position in game
        # visualModel - SceneGraphNode of the ship visual model
        super().__init__(name, x, y, time, visualModel, 1)
        self.trayectory = trayectory
        self.orbitMovement = None

    def spawnShot(self, time):
        # Spawn an enemy shot
        # time - current clock time in seconds
        self.lastShot = time
        return EnemyShot(self.currentX, self.currentY - self.shipHalfHeight)

    def updatePos(self, time):
        # Update enemy ship position
        # time - current clock time in seconds
        if not self.trayectory.finished:
            # Follow trayectory until finished
            self.currentX, self.currentY = self.trayectory.get_pos(time)
        else:
            # Then orbit around the endpoint of the trayectory
            if self.orbitMovement is None:
                self.orbitMovement = gu.Orbit(center=self.currentX,
                                              radius=self.orbitRadius,
                                              speed=self.orbitSpeed,
                                              time=time)
            self.currentX = self.orbitMovement.get_pos(time)
            
    def update(self,time):
        # time - current clock time in seconds
        if self.state == S_ALIVE:
            # Update ship position
            self.updatePos(time)
            self.updateVisualPos()
        elif self.state == S_HIT:
            self.manageHitState(time)

# A class to manage the player ship
class Player(Ship):
    firePeriod = 0.8
    shipHalfWidth = 0.08
    shipHalfHeight = 0.05
    playerSpeed = 1.0

    def __init__(self, name, x, y, time, controller, visualModel):
        # name - Name of the ship
        # x - Start x position in game
        # y - Start y position in game
        # time - current clock time in seconds
        # controller - Controller instance of the game
        # visualModel - SceneGraphNode of the ship visual model
        super().__init__(name, x, y, time, visualModel, 3)
        self.controller = controller

    def spawnShot(self, time):
        # time - current clock time in seconds
        # Spawn a player shot
        self.lastShot = time
        return PlayerShot(self.currentX, self.currentY + self.shipHalfHeight)

    def movePlayer(self, dt):
        # dt - Game frame time difference in seconds
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
        # time - current clock time in seconds
        # dt - Game frame time difference in seconds
        if self.state == S_ALIVE:
            # Update player position
            self.movePlayer(dt)
            self.updateVisualPos()
        elif self.state == S_HIT:
            self.manageHitState(time)

# A class to manage game state
class GameModel:
    def __init__(self, nEnemies, screenWidth, screenHeight, controller):
        # nenemies - Number of enemies to spawn
        # screenWidth - Game screen width
        # screenHeight - Game screen height
        # controller - Controller instance of the game

        # Start clock
        self.ltime = 0.0
        # reference to the gaplayerme controller

        # Create game scene
        self.gameScene = sg.SceneGraphNode("gameScene")
        self.gameScene.transform = tr.scale(screenHeight/ screenWidth, 1.0, 1.0)

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
        # Function to check if a shot hits any 
        # shot - A PlayerShot object
        # time - current clock time in seconds 
        for enemy in self.enemies:
            if enemy.isHit(shot, time):
                return True
        return False

    def moveShots(self, time, dt):
        # Function to move shots on the game and check
        # time - current clock time in 
        # dt - Game frame time difference in seconds
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
        # time - current clock time in seconds
        
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
        # time - current clock time in seconds
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
                    shot = enemy.spawnShot(time)
                    shot.setVisual(self.enemyShotModel)
                    self.enemyShots.append(shot)
            elif enemy.state == S_HIT:
                # Set explosion model
                enemy.setVisual(self.explosionmodel)
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
        # Method to manage the player ship
        # time - current clock time in seconds
        # dt - Game frame time difference in seconds
        # interaction
        self.player.update(time, dt)
        if self.player.state == S_ALIVE:
            # manage shots
            if self.player.controller.fire and self.player.canShoot(time):
                shot = self.player.spawnShot(time)
                shot.setVisual(self.playerShotModel)
                self.playerShots.append(shot)
        elif self.player.state == S_HIT:
            self.player.setVisual(self.explosionmodel)
            self.state = G_LOST

    def updateGame(self, time):
        # Method to update all the game state
        # time - current clock time in seconds
        dt = time - self.ltime
        self.ltime = time
        # Update each game elements
        self.moveShots(time, dt)
        self.manageEnemies(time)
        self.managePlayer(time, dt)

    def getGameScene(self):
        # Method to obtain scene graph with the current ships and shots in screen
        screenElements = []
        for ship in [self.player]+self.enemies:
            if ship.state != S_DEAD:
                screenElements.append(ship.sceneNode)
        for shot in self.enemyShots+self.playerShots:
            if shot.inScreen:
                screenElements.append(shot.sceneNode)
        screenElements.append(self.hpStatusDraw())
        self.gameScene.childs = screenElements
        return self.gameScene
        
