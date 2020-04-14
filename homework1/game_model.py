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

# A class to manage each enemy
class Enemy:
    def __init__(self, x, y, time, trayectory, visualModel):
        self.currentX = x
        self.currentY = y
        self.state = S_ALIVE
        self.lastShot = time
        self.deathTime = None
        self.trayectory = trayectory
        self.visual = visualModel

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
            self.currentX, self.currentY = self.trayectory.get_pos(time)
        elif self.state == S_HIT:
            if self.deathTime is None:
                self.deathTime = time
            elif (time-self.deathTime) > 0.2:
                self.state = S_DEAD

# A class to manage game state
class GameModel:
    def __init__(self, nEnemies, screenWidht, screenHeight, controller):
        # Start clock
        self.ltime = 0.0
        # reference to the game controller
        self.controller = controller
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
        self.playerX = 0.0
        self.playerY = -0.75
        self.player = sg.SceneGraphNode("Player")
        self.player.transform = tr.translate(self.playerX, self.playerY, 0.0)
        self.player.childs = [self.playerModel]

        self.playerState = S_ALIVE
        self.playerSpeed = 1.0
        self.playerLSTime = 0.0
        self.playerFR = 0.8
        self.playerHitTime = None
        self.playerHP = 3

        # Objects list
        self.playerShots = []
        self.enemyShots = []
        self.enemies = []

        # Game status
        self.gameover = False
        self.remainingEnemies = nEnemies
        self.wave = 0
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
        self.playerY = np.clip(self.playerY,-0.9,0.4)

    def spawnPlayerShot(self):
        self.playerShots.append(PlayerShot(self.playerX,self.playerY+0.1))

    def checkEnemyHit(self, shot):
        for enemy in self.enemies:
            if enemy.state == S_ALIVE and gu.checkHitbox(shot.currentX, shot.currentY, 
                                            enemy.currentX-0.08, enemy.currentY+0.05,
                                            enemy.currentX+0.08, enemy.currentY-0.05):
                enemy.state = S_HIT
                return True
        return False

    def checkPlayerHit(self, shot):
        if self.playerState == S_ALIVE:
            if gu.checkHitbox(shot.currentX, shot.currentY, 
                    self.playerX-0.08, self.playerY+0.05,
                    self.playerX+0.08, self.playerY-0.05):
                self.playerHP -= 1
                if self.playerHP == 0:
                    self.gameover = True
                    self.playerState = S_HIT
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
        elif self.remainingEnemies > 0 and (time-self.lastEnemyTimer) > 1.0:
            self.wave += 1
            toSpawn = min(np.clip(self.wave, 0, 5), self.remainingEnemies)
            x = np.arange(0, (toSpawn)*0.25, 0.25) - (toSpawn-1)*0.125
            x2 = x[gu.derangement(len(x))]
            waveModel = self.wave%3
            for i in range(toSpawn):
                trayectory = gu.LinearTrayectory(time, 1.5, x[i], 1.1, x2[i], 0.4)
                enemyShip = Enemy(x[i], 0.9, time + np.random.random(), trayectory, self.enemyModels[waveModel])
                self.enemies.append(enemyShip)
                self.remainingEnemies -= 1
            self.waitSpawn = False

    def manageEnemies(self, time):
        # Function to update enemies status
        if len(self.enemies) == 0:
            self.spawnEnemies(time)
        screenEnemies = []
        currentEnemies = []
        for i,enemy in enumerate(self.enemies):
            enemy.update(time)
            if enemy.state == S_ALIVE:
                # spawn enemy shoot
                if enemy.shouldShoot(time):
                    self.enemyShots.append(enemy.spawnShot())
                screenEnemy = sg.SceneGraphNode(f"enemy_{i}")
                screenEnemy.transform = tr.translate(enemy.currentX,enemy.currentY,0.0)
                screenEnemy.childs = [enemy.visual]
                screenEnemies.append(screenEnemy)
                currentEnemies.append(enemy)
            elif enemy.state == S_HIT:
                screenEnemy = sg.SceneGraphNode(f"dead_enemy_{i}")
                screenEnemy.transform = tr.translate(enemy.currentX,enemy.currentY,0.0)
                screenEnemy.childs = [self.explosionmodel]
                screenEnemies.append(screenEnemy)
                currentEnemies.append(enemy)
        self.enemies = currentEnemies
        return screenEnemies

    def playerInteraction(self,time, dt):
        if not self.gameover:
            # Update player position
            self.movePlayer(dt)
            self.player.transform = tr.translate(self.playerX, self.playerY, 0.0)
            # manage shots
            if self.controller.fire and (time - self.playerLSTime)>self.playerFR:
                self.spawnPlayerShot()
                self.playerLSTime = time
        elif self.playerState == S_HIT:
            if self.playerHitTime is None:
                self.playerHitTime = time
            elif (time - self.playerHitTime) > 0.2:
                self.playerState = S_DEAD

    def playerDraw(self):
        if self.playerState == S_ALIVE:
            return [self.player]
        elif self.playerState == S_HIT:
            explosion = sg.SceneGraphNode("Dead_player")
            explosion.transform = tr.translate(self.playerX, self.playerY, 0.0)
            explosion.childs = [self.explosionmodel]
            return [explosion]
        else:
            return []

    def hpStatusDraw(self):
        hpBar = sg.SceneGraphNode("hp_bar")
        hpBar.childs = []
        x = np.arange(0, (self.playerHP)*0.07, 0.07)
        for i in range(self.playerHP):
            hpBlock = sg.SceneGraphNode(f"hp_{i}")
            hpBlock.transform = tr.translate(x[i], 0.0, 0.0)
            hpBlock.childs = [self.hpBlockModel]
            hpBar.childs.append(hpBlock)
        hpStatus = sg.SceneGraphNode("hp_status")
        hpStatus.transform = tr.translate(-0.65, 0.9, 0.0)
        hpStatus.childs = [hpBar]
        return [hpStatus]

    def updateScene(self, time):#084177#084177
        dt = time - self.ltime
        self.ltime = time
        

        screenShots = self.moveShots(dt)

        screenEnemies = self.manageEnemies(time)

        self.playerInteraction(time, dt)
        
        screenPlayer = self.playerDraw()

        screenHPBar = self.hpStatusDraw()
        self.gameScene.childs = screenPlayer + screenShots + screenEnemies + screenHPBar
        #print(sg.findPosition(player,"Player"))
        return self.gameScene