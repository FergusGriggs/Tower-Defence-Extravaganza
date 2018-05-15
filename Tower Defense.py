###td

import pygame, sys, math, random, pygame.midi, time
from pygame.locals import *
from operator import itemgetter

screenW=1000
screenH=800
screen = pygame.display.set_mode((screenW, screenH))
background=pygame.Surface((screenW,screenH))
pygame.display.set_caption('td')
pygame.init()


pygame.midi.init()
player= pygame.midi.Output(0)
player.set_instrument(97,1)

complexSurface=pygame.Surface((screenW,screenH))
complexSurface.set_colorkey((0,0,0))
complexSurface2=pygame.Surface((200,screenH))
complexSurface2.set_colorkey((0,0,0))
for i in range(10000):
    n=random.randint(240,255)
    pygame.draw.circle(complexSurface,(n-n/4,n-n/8,n),(random.randint(0,screenW),random.randint(0,screenH)),random.randint(2,30),0)
for i in range(10000):
    n=random.randint(240,255)
    pygame.draw.circle(complexSurface2,(n,n-n/4,n-n/8),(random.randint(0,screenW),random.randint(0,screenH)),random.randint(2,30),0)
class Enemy():
    def __init__(self,EnemyType,Path):
        self.x=-1000#xcoord
        self.y=-1000#ycoord
        self.type=EnemyType#type object for the enemy
        self.path=Path#path the enemy will follow
        self.maxHp=EnemyType.hp#max hp of the enemy
        self.hp=EnemyType.hp#current hp of the enemy
        self.hpDecimal=1#hp as a decimal
        self.hpColour=(0,255,0)#colour of hp
        self.showHpBar=False#is the hp bar showing
        self.speed=EnemyType.speed+random.randint(-100,100)/500#speed from type object but slightly changed for each instance
        self.time=0#time since last point in path
        self.pointPos=0#last point traversed
        self.pathOffsetX=random.randint(-8,8)
        self.pathOffsetY=random.randint(-8,8)
        self.isCarrier=EnemyType.isCarrier
        self.colour=EnemyType.colour
        self.size=EnemyType.size
        self.damageVal=EnemyType.damage
        self.score=EnemyType.score
        self.speedMod=1
        self.speedModTimer=0
        self.freeze=False
        self.freezeTimer=0
        self.burn=False
        self.burnTicks=0
        self.burnTimer=0
        self.burnDelay=0
        self.burnDMG=0
        self.electrified=False
        self.carrierSpread=False
        if self.isCarrier:
            self.carrierNum=EnemyType.carrierNum
            self.carrierType=EnemyType.carrierType
    def update(self):
        global lives, gameState, enemies, showPopUpMenu, scrollItems
        self.x=self.path.points[self.pointPos][0]+((self.path.points[self.pointPos+1][0]-self.path.points[self.pointPos][0])/path.times[self.pointPos])*self.time+self.pathOffsetX
        self.y=self.path.points[self.pointPos][1]+((self.path.points[self.pointPos+1][1]-self.path.points[self.pointPos][1])/path.times[self.pointPos])*self.time+self.pathOffsetY
        self.electrified=False
        if not self.freeze:
            if self.speedModTimer >0:
                self.time+=self.speed*self.speedMod
                self.speedModTimer-=1
            else:
                 self.time+=self.speed
        elif self.freeze:
            if self.freezeTimer>0:
                self.freezeTimer-=1
            else:
                self.freeze=False
        if self.burn:
            if self.burnTimer>0:
                self.burnTimer-=1
            else:
                self.burnTimer=self.burnDelay
                if self.burnTicks>0:
                    self.burnTicks-=1
                    self.damage(self.burnDMG)
                else:
                    self.burn=False
                
        if self.time>path.times[self.pointPos]:
            self.time=self.time-path.times[self.pointPos]
            if self.pointPos<len(path.points)-2:
                self.pointPos+=1
            else:
                enemies.remove(self)
                lives-=self.damageVal
                if lives<=0:
                    lives=0
                    gameState="over"
                    showPopUpMenu=False
                    scrollItems=5
                
    def draw(self):
        if self.burn:
            pygame.draw.circle(screen,(255,0,0),(int(self.x),int(self.y)),self.size,0)
        elif self.freeze:
            pygame.draw.circle(screen,(64,224,208),(int(self.x),int(self.y)),self.size,0)
        else:
            pygame.draw.circle(screen,self.colour,(int(self.x),int(self.y)),self.size,0)
    def drawHpBar(self):
        pygame.draw.rect(screen,self.hpColour,(self.x-15,self.y-self.size-10,30*self.hpDecimal,5),0)
        pygame.draw.rect(screen,self.hpColour,(self.x-15,self.y-self.size-10,30,5),1)
    def damage(self,value):
        global enemies, score, gold, enemiesKilled
        self.hp-=value
        if self.hp<=0:
            if self.isCarrier:
                for i in range(self.carrierNum):
                    e=Enemy(self.carrierType,self.path)
                    e.pointPos=self.pointPos
                    e.time=self.time
                    if self.burn:
                        e.burn=True
                        e.burnTicks=self.burnTicks
                        e.burnTimer=self.burnTimer
                        e.burnDelay=self.burnDelay
                        e.burnDMG=self.burnDMG
                    if not self.carrierSpread:
                        e.pathOffsetX=self.pathOffsetX
                        e.pathOffsetY=self.pathOffsetY
                    enemies.append(e)
                    e.damage(abs(self.hp)/self.carrierNum)
            else:
                if gameState=="playing":
                    enemiesKilled+=1
            if self in enemies:
                enemies.remove(self)
                playDeathSound()
            if gameState=="playing":
                score+=self.score
                gold+=int(self.score*0.2)
        if self.hp<=0:
            self.hp=0
        self.hpDecimal=(self.hp/self.maxHp)
        self.hpColour=(255*(1-self.hpDecimal),255*self.hpDecimal,0)
        if self.hp==self.maxHp:
            self.showHpBar=False
        else:
            self.showHpBar=True
    def electrify(self,maxCount,count,DMG):
        if count>0:
            count-=1
            for enemy in enemies:
                if not enemy.electrified and enemy.hp>0 and enemy != self:
                    if distance(enemy.x,enemy.y,self.x,self.y)<50:
                        pygame.draw.line(screen,(255,255,0),(self.x,self.y),(enemy.x,enemy.y),2)
                        self.electrified=True
                        enemy.damage(DMG*(count/maxCount))
                        print(DMG*(count/maxCount))
                        enemy.electrify(maxCount,count,DMG)
                        return
        else:
            return
class EnemyType():
    def __init__(self,hp,speed,carrier,carrierNum,carrierType,colour,size,damage,score):
        self.hp=hp
        self.speed=speed
        self.isCarrier=carrier
        self.colour=colour
        self.size=size
        self.damage=damage
        self.score=score
        if self.isCarrier:
            self.carrierNum=carrierNum
            self.carrierType=carrierType
class TowerType():
    def __init__(self,damage,speed,fireRange,slow,freeze,burn,electric,colour,targetPref,name,targets,initialCost,DMGLVLS,FiRaLVLS,RaLVLS):
        self.damage=damage
        self.speed=speed
        self.range=fireRange
        self.slow=slow
        self.freeze=freeze
        self.burn=burn
        self.electric=electric
        self.colour=colour
        self.targetPref=targetPref
        self.name=name
        self.targets=targets
        self.initialCost=initialCost
        self.DMGLVLS=DMGLVLS
        self.FiRaLVLS=FiRaLVLS
        self.RaLVLS=RaLVLS
class Map():
    def __init__(self,paths,waves):
        self.paths=paths
        self.waves=waves
class Burst():
    def __init__(self,enemyType,count,amt,delay,repeatNum,repeatDelay):
        global baseEnemyTypes
        self.type=enemyType
        self.amount=amt
        self.count=count
        self.delay=delay
        self.time=0
        self.burstNum=0
        self.repeatCount=0
        self.repeatNum=repeatNum
        self.repeatDelay=repeatDelay
        self.done=False
    def update(self):
        global deltaTime, currentMap
        self.time+=deltaTime
        if self.time>self.delay:
            if self.burstNum<self.count:
                self.burstNum+=1
                self.time=0
                createEnemies(self.amount,self.type,maps[currentMap].paths)
            else:
                if self.repeatCount<self.repeatNum:
                    self.burstNum=0
                    self.repeatCount+=1
                    self.time=self.delay-self.repeatDelay
                else:
                    self.done=True   
        
class Path():
    def __init__(self,points):
        self.points=points
        self.times=[0 for i in range(len(points)-1)] 
        for i in range(len(points)-1):
            self.times[i]=distance(self.points[i][0],self.points[i][1],self.points[i+1][0],self.points[i+1][1])
class Tower():
    def __init__(self,x,y,TowerType):
        self.x=x
        self.y=y
        self.type=TowerType
        self.damage=TowerType.damage
        self.speed=TowerType.speed*random.randint(950,1050)/1000
        self.range=TowerType.range
        self.slow=TowerType.slow
        self.freeze=TowerType.freeze
        self.burn=TowerType.burn
        self.electric=TowerType.electric
        self.colour=TowerType.colour
        self.targetPref=TowerType.targetPref
        self.name=TowerType.name
        self.targets=TowerType.targets
        self.delay=self.speed
        self.canFire=True
        self.target=None
        self.aimAngle=0
        self.DMGLVL=0
        self.FiRaLVL=0
        self.RaLVL=0
        self.totalSpent=TowerType.initialCost
    def update(self):
        global enemies
        if self.delay<0:
            self.canFire=True
        else:
            self.delay-=1
        runTargetLoop=False
        targets=[]
        for enemy in enemies:
            if distance(self.x,self.y,enemy.x,enemy.y)<self.range+enemy.size and self.canFire:
                targets.append(enemy)
                runTargetLoop=True
        
        if self.targets>0:
            if runTargetLoop:
                if self.targetPref==0:#front
                    timemaxes=[ 0 for i in range(100)]
                    pointMax=0
                    for i in range(len(targets)):
                        if targets[i].pointPos>=pointMax:
                            pointMax=targets[i].pointPos
                            if targets[i].time>=timemaxes[targets[i].pointPos]:
                                timemaxes[targets[i].pointPos]=targets[i].time
                                chosenTarget=targets[i]
                elif self.targetPref==1:#back
                    timemins=[ 1000000000 for i in range(100)]
                    pointMin=10000000
                    for i in range(len(targets)):
                        if targets[i].pointPos<=pointMin:
                            pointMin=targets[i].pointPos
                            if targets[i].time<=timemins[targets[i].pointPos]:
                                timemins[targets[i].pointPos]=targets[i].time
                                chosenTarget=targets[i]
                
                elif self.targetPref==2:#maxhp
                    maxhp=0
                    for i in range(len(targets)):
                        if targets[i].hp>=maxhp:
                            maxhp=targets[i].hp
                            chosenTarget=targets[i]
                elif self.targetPref==3:#min hp
                    minhp=100000000000
                    for i in range(len(targets)):
                        if targets[i].hp<=minhp:
                            minhp=targets[i].hp
                            chosenTarget=targets[i]
                self.target=chosenTarget
                self.aimAngle=math.atan2(self.target.y-self.y,self.target.x-self.x)
                if self.slow==True:
                    chosenTarget.speedMod=0.4
                    chosenTarget.speedModTimer=150
                if self.type==towerTypes[6]:
                    for enemy in enemies:
                        if enemy != chosenTarget:
                            if distance(enemy.x,enemy.y,chosenTarget.x,chosenTarget.y)<30:
                                enemy.damage(self.damage)
                    pygame.draw.circle(screen,(255,0,0),(int(chosenTarget.x),int(chosenTarget.y)),30,0)
                    chosenTarget.damage(self.damage)
                if self.burn:
                    chosenTarget.burn=True
                    chosenTarget.burnTimer=0
                    chosenTarget.burnDMG=self.damage
                    chosenTarget.burnTicks=20
                    chosenTarget.burnDelay=6
                elif self.electric:
                    chosenTarget.damage(self.damage)
                    chosenTarget.electrify(20,20,self.damage)
                else:
                    chosenTarget.damage(self.damage)
                if self.type==towerTypes[0]:
                    playFireSound("normie")
                elif self.type==towerTypes[1]:
                    playFireSound("back burner")
                elif self.type==towerTypes[2]:
                    playFireSound("sniper")
                elif self.type==towerTypes[3]:
                    playFireSound("machine gun")
                elif self.type==towerTypes[5]:
                    playFireSound("glue gun")
                elif self.type==towerTypes[6]:
                    playFireSound("bomb shooter")
                elif self.type==towerTypes[7]:
                    playFireSound("tesla cannon")
        
                
                self.canFire=False
                self.delay=self.speed
                if self.name=="tesla cannon":
                    pygame.draw.line(screen,(255,255,0),(self.x,self.y),(chosenTarget.x,chosenTarget.y),2)
                else:
                    pygame.draw.line(screen,(255,0,0),(self.x,self.y),(chosenTarget.x,chosenTarget.y),2)
            runTargetLoop=False
        else:
            if runTargetLoop:
                for enemy in targets:
                    enemy.freezeTimer=20
                    if not enemy.freeze:
                        enemy.freeze=True
                    enemy.damage(self.damage)
                playFireSound("freezer")
                self.canFire=False
                self.delay=self.speed
            
    def draw(self):
        pygame.draw.circle(screen,self.colour,(self.x,self.y),10,0)
        if gameState=="playing" or gameState=="placing":
            if not self.freeze:
                pygame.draw.line(screen,(255,0,0),(self.x,self.y),(self.x+math.cos(self.aimAngle)*10,self.y+math.sin(self.aimAngle)*10),2)
                #pygame.draw.polygon(screen,self.colour,[(self.x+math.cos(self.aimAngle-math.pi/4)*15,self.y+math.sin(self.aimAngle-math.pi/4)*15),(self.x+math.cos(self.aimAngle+math.pi/4)*15,self.y+math.sin(self.aimAngle+math.pi/4)*15),(self.x+math.cos(self.aimAngle-0.2)*15,self.y+math.sin(self.aimAngle-0.2)*15),(self.x+math.cos(self.aimAngle+0.2)*15,self.y+math.sin(self.aimAngle+0.2)*15)],0)
def placeTower(x,y,TowerType):
    global towers
    towers.append(Tower(x,y,TowerType))
    
def createTowers(num,TowerType):
    global towers
    for i in range(num):
        towers.append(Tower(random.randint(0,screenW),random.randint(0,screenH),TowerType))
def drawTowers():
    global towers
    for tower in towers:
        tower.draw()
def updateTowers():
    global towers
    for tower in towers:
        tower.update()
def drawTowerRanges():
    global towers
    for tower in towers:
        pygame.draw.circle(screen,(0,0,0),(tower.x,tower.y),tower.range,1)
def createEnemies(num,EnemyType,path):
    global enemies
    for i in range(num):
        enemies.append(Enemy(EnemyType,path))
def updateEnemies():
    global enemies, gameState
    for enemy in enemies:
        enemy.update()
def drawEnemies():
    global enemies
    for enemy in enemies:
        enemy.draw()
        if enemy.showHpBar:
            enemy.drawHpBar()
            
def distance(x1,y1,x2,y2):
    return math.sqrt((x2-x1)**2+(y2-y1)**2)
def createBackground(Map):
    global background
    background= pygame.Surface((screenW,screenH))
    background.fill((255,255,255))
    background.blit(complexSurface,(0,0))
    for j in range(len(Map.paths.points)):
        pygame.draw.circle(background,(65,105,225),(int(Map.paths.points[j][0]),int(Map.paths.points[j][1])),20,0)
    pygame.draw.lines(background,(65,105,225),False,Map.paths.points,30)
    background.blit(complexSurface2,(800,0))
    pygame.draw.line(background,(100,100,100),(801,0),(801,800),4)
    pygame.draw.line(background,(65,105,225),Map.paths.points[0],Map.paths.points[1],29)
    #pygame.draw.rect(background,(220,220,220),Rect(800,0,200,800),0)
    pygame.draw.rect(background,(150,150,150),Rect(806,0,194,245),0)
    pygame.draw.line(background,(100,100,100),(800,0),(800,250),10)
    pygame.draw.line(background,(100,100,100),(796,245),(1000,245),10)
    backFont = pygame.font.Font("Fonts/Robot Crush.otf",20)
    backText=backFont.render("mouse over here to",True,(0,0,0))
    backText2=backFont.render("buy some towers",True,(0,0,0))
    background.blit(backText,(900-backText.get_width()/2,575))
    background.blit(backText2,(900-backText2.get_width()/2,600))
def cursorDamage():
    for enemy in enemies:    
        if distance(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1],enemy.x,enemy.y)<50:
            enemy.damage(1)
    pygame.draw.circle(screen,(0,0,0),pygame.mouse.get_pos(),50,1)
def drawLives():
    global lives
    lifeFont = pygame.font.Font("Fonts/Robot Crush.otf",35)
    lifeText=lifeFont.render(str(lives),True,(255,0,0))
    screen.blit(lifeText,(screenW-10-lifeText.get_width(),160))
def drawScore():
    global score
    scoreFont = pygame.font.Font("Fonts/Robot Crush.otf",35)
    scoreText=scoreFont.render(str(int(score*(1+time/1000000)))+" pts",True,(0,0,0))
    screen.blit(scoreText,(screenW-10-scoreText.get_width(),195))
def drawGold():
    global gold
    goldFont = pygame.font.Font("Fonts/Robot Crush.otf",35)
    goldText=goldFont.render("£"+str(int(gold)),True,(255,215,0))
    screen.blit(goldText,(810,160))
def drawPlayerName():
    global playerName
    playerFont = pygame.font.Font("Fonts/Robot Crush.otf",35)
    playerText=playerFont.render("playing as:",True,(0,0,0))
    playerText2=playerFont.render(str(playerName),True,(218,165,32))
    screen.blit(playerText,(10,10))
    screen.blit(playerText2,(10,40))
def drawKillCount():
    global enemiesKilled
    if gameState=="playing":
        killFont = pygame.font.Font("Fonts/Robot Crush.otf",35)
        killText=killFont.render("enemies killed: "+str(enemiesKilled),True,(0,0,0))
        screen.blit(killText,(0,35))
def drawTimes():
    global time
    time1=int((time/1000)//60)
    time2=(time/1000)%60
    if time1<10:
        time1="0"+str(time1)
    else:
        time1=str(round(time1,1))
    if time2<10:
        time2="0"+str(round(time2,2))
    else:
        time2=str(round(time2,1))
    
    timeFont = pygame.font.Font("Fonts/Robot Crush.otf",35)
    if gameState=="playing":
        timeText=timeFont.render("Time survived: "+time1+":"+time2,True,(0,0,0))
        screen.blit(timeText,(0,0))
def updateTime():
    global time, deltaTime
    time+=deltaTime
def drawEndScreen():
    global score, time
    time1=int((time/1000)//60)
    time2=(time/1000)%60
    if time1<10:
        time1="0"+str(time1)
    else:
        time1=str(time1)
    if time2<10:
        time2="0"+str(round(time2,2))
    else:
        time2=str(round(time2,2))
    scoreFont = pygame.font.Font("Fonts/Robot Crush.otf",50)
    bigScoreFont = pygame.font.Font("Fonts/Robot Crush.otf",75)
    scoreText0=bigScoreFont.render(str(playerName+","),True,(0,0,0))
    scoreText1=scoreFont.render("You lasted "+time1+":"+time2+" scoring",True,(0,0,0))
    scoreText2=scoreFont.render("a whopping "+str(int(score*(1+time/1000000)))+" points using",True,(0,0,0))
    scoreText3=scoreFont.render(str(len(towers))+" towers, killing "+str(enemiesKilled)+" enemies!",True,(0,0,0))
    scoreText4=bigScoreFont.render("your rank: "+str(playerRank),True,(0,0,0))
    scoreText5=scoreFont.render("press space for another go!",True,(0,0,0))
    screen.blit(scoreText0,(400-scoreText0.get_width()/2,25))
    screen.blit(scoreText1,(400-scoreText1.get_width()/2,125))
    screen.blit(scoreText2,(400-scoreText2.get_width()/2,175))
    screen.blit(scoreText3,(400-scoreText3.get_width()/2,225))
    screen.blit(scoreText4,(400-scoreText4.get_width()/2,305))
    screen.blit(scoreText5,(400-scoreText5.get_width()/2,730))
def checkHover():
    global towers, pressing, showPopUpMenu
    for tower in towers:
        if distance(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1],tower.x,tower.y)<10:
            if pygame.mouse.get_pressed()[0]:
                if not pressing and not showPopUpMenu:
                    createPopUpMenu(tower.x,tower.y,tower)
            if not showPopUpMenu:
                pygame.draw.circle(screen,(0,0,0),(tower.x,tower.y),tower.range,1)
                towerFont = pygame.font.Font("Fonts/Robot Crush.otf",15)
                towerText=towerFont.render(tower.name,True,(0,0,0))
                screen.blit(towerText,(tower.x-towerText.get_width()/2,tower.y-30))
def drawBuyMenu():
    global buttons, gold, showPopUpMenu
    pygame.draw.rect(screen,(150,150,150),(800,410,200,470),0)
    pygame.draw.line(screen,(100,100,100),(800,410),(800,800),10)
    pygame.draw.line(screen,(100,100,100),(796,410),(1000,410),10)
    for button in buttons:
        if gold>=button.type.initialCost:
            if button.rect.collidepoint(pygame.mouse.get_pos()) and not showPopUpMenu and gameState != "over":    
                pygame.draw.rect(screen,(255,255,153),button.rect,0)
            else:
                pygame.draw.rect(screen,button.colour,button.rect,0)
            pygame.draw.rect(screen,(0,255,0),button.rect,3)
        else:
            pygame.draw.rect(screen,(255,0,0),button.rect,3)
        pygame.draw.circle(screen,button.type.colour,(button.rect.left+45,button.rect.top+50),15,0)
        towerMenuFont = pygame.font.Font("Fonts/Robot Crush.otf",25-len(button.title))
        towerMenuText=towerMenuFont.render(button.title,True,(0,0,0))
        screen.blit(towerMenuText,(button.rect.left+45-towerMenuText.get_width()/2,button.rect.top+5))
def fadeScreen():
    global fadeSurface, screenW, screenH
    screen.blit(fadeSurface,(0,0))
def checkMousePos():
    global buttons, pressing, newTower, popUpButtons, popUpPressing, showPopUpMenu, gold, towers, gameState, allData, scrollItems, buttonAccValues, backButton
    if gameState=="playing" or gameState=="placing":
        for button in buttons:
            if button.rect.collidepoint(pygame.mouse.get_pos()):
                if gold>=button.type.initialCost and not showPopUpMenu and gameState != "over":
                    pressing=True
                    newTower=button.type
        for button in popUpButtons:
            if button.rect.collidepoint(pygame.mouse.get_pos()):
                if button.title=="quit":
                    showPopUpMenu=False
                elif button.title=="sell":
                    if button.tower in towers:
                        towers.remove(button.tower)
                        gold+=int(button.tower.totalSpent*0.8)
                        playBuySound(1,10)
                    showPopUpMenu=False
                elif button.title=="up dmg":
                    if not popUpPressing:
                        popUpPressing=True
                        if button.tower.DMGLVL<len(button.tower.type.DMGLVLS):
                            if gold>=button.tower.type.DMGLVLS[button.tower.DMGLVL][1]:
                                gold-=button.tower.type.DMGLVLS[button.tower.DMGLVL][1]
                                button.tower.damage=button.tower.type.DMGLVLS[button.tower.DMGLVL][0]
                                button.tower.totalSpent+=button.tower.type.DMGLVLS[button.tower.DMGLVL][1]
                                playBuySound(button.tower.DMGLVL,len(button.tower.type.DMGLVLS))
                                button.tower.DMGLVL+=1
                            else:
                                playRejectSound()
                elif button.title=="up fire rate":
                    if not popUpPressing:
                        popUpPressing=True
                        if button.tower.FiRaLVL<len(button.tower.type.FiRaLVLS):
                            if gold>=button.tower.type.FiRaLVLS[button.tower.FiRaLVL][1]:
                                gold-=button.tower.type.FiRaLVLS[button.tower.FiRaLVL][1]
                                button.tower.speed=button.tower.type.FiRaLVLS[button.tower.FiRaLVL][0]
                                button.tower.totalSpent+=button.tower.type.FiRaLVLS[button.tower.FiRaLVL][1]
                                playBuySound(button.tower.FiRaLVL,len(button.tower.type.FiRaLVLS))
                                button.tower.FiRaLVL+=1
                            else:
                                playRejectSound()
                elif button.title=="up range":
                    if not popUpPressing:
                        popUpPressing=True
                        if button.tower.RaLVL<len(button.tower.type.RaLVLS):
                            if gold>=button.tower.type.RaLVLS[button.tower.RaLVL][1]:
                                gold-=button.tower.type.RaLVLS[button.tower.RaLVL][1]
                                button.tower.range=button.tower.type.RaLVLS[button.tower.RaLVL][0]
                                button.tower.totalSpent+=button.tower.type.RaLVLS[button.tower.RaLVL][1]
                                playBuySound(button.tower.RaLVL,len(button.tower.type.RaLVLS))
                                button.tower.RaLVL+=1
                            else:
                                playRejectSound()
                elif button.title=="change priority":
                    if not popUpPressing:
                        popUpPressing=True
                        if button.tower.targetPref<3:
                            button.tower.targetPref+=1
                        else:
                            button.tower.targetPref=0
                        playClickSound()
    elif gameState=="menu":
        if pygame.mouse.get_pressed()[0]:
            for button in menuButtons:
                if button.rect.collidepoint(pygame.mouse.get_pos()):
                    if button.title=="start" and not pressing:
                        gameState="placing"
                        restartGame()
                    elif button.title=="leaderboard" and not pressing:
                        gameState="menulb"
                        scrollItems=8
                        allData=handleRank(None,False)
                    elif button.title=="quit" and not pressing:
                        pygame.quit()
                        sys.exit()
    elif gameState=="menulb":
        backFont = pygame.font.Font("Fonts/Robot Crush.otf",50)
        backText=backFont.render("back",True,(0,0,0))
        if backButton.rect.collidepoint(pygame.mouse.get_pos()):
            buttonAccValues["back"][0]+=buttonAccValues["back"][1]
            if buttonAccValues["back"][1]>0:
                buttonAccValues["back"][1]-=0.1
            else:
                buttonAccValues["back"][1]=0
            col=(190,190,190)
            pygame.draw.ellipse(screen,col,Rect(backButton.rect.left-1*buttonAccValues["back"][0],backButton.rect.top-1*buttonAccValues["back"][0],backButton.rect.width+2*buttonAccValues["back"][0],backButton.rect.height+2*buttonAccValues["back"][0]),0)
            if pygame.mouse.get_pressed()[0]:
                pressing=True
                gameState="menu"
                playClickSound()
        else:
            if buttonAccValues["back"][0]>0:
                buttonAccValues["back"][0]-=buttonAccValues["back"][1]
                buttonAccValues["back"][1]+=0.1
            else:
                buttonAccValues["back"][0]=0
                buttonAccValues["back"][1]=1.5
            col=(220,220,220)
            pygame.draw.ellipse(screen,col,Rect(backButton.rect.left-1*buttonAccValues["back"][0],backButton.rect.top-1*buttonAccValues["back"][0],backButton.rect.width+2*buttonAccValues["back"][0],backButton.rect.height+2*buttonAccValues["back"][0]),0)
        screen.blit(backText,(500-backText.get_width()/2,715))
                        
class Button():
    def __init__(self,rect,TowerType,title,refrencetower):
        self.rect=rect
        self.colour=(230,230,230)
        self.type=TowerType
        self.title=title
        self.tower=refrencetower
def drawNewTower():
    global pressing, newTower
    if pressing:
        if checkValidPos(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1]):
            pygame.draw.circle(screen,newTower.colour,pygame.mouse.get_pos(),10,0)
            pygame.draw.circle(screen,(0,0,0),pygame.mouse.get_pos(),newTower.range,1)
            towerFont = pygame.font.Font("Fonts/Robot Crush.otf",15)
            towerText=towerFont.render(newTower.name,True,(0,0,0))
            screen.blit(towerText,(pygame.mouse.get_pos()[0]-towerText.get_width()/2,pygame.mouse.get_pos()[1]-30))
        else:
            pygame.draw.line(screen,(255,0,0),(pygame.mouse.get_pos()[0]-10,pygame.mouse.get_pos()[1]-10),(pygame.mouse.get_pos()[0]+10,pygame.mouse.get_pos()[1]+10),2)
            pygame.draw.line(screen,(255,0,0),(pygame.mouse.get_pos()[0]+10,pygame.mouse.get_pos()[1]-10),(pygame.mouse.get_pos()[0]-10,pygame.mouse.get_pos()[1]+10),2)
def createPopUpMenu(x,y,tower):
    global popUpButtons, showPopUpMenu
    popUpButtons=[]
    showPopUpMenu=True
    popUpButtons.append(Button(Rect(x-100,y-75,45,45),None,"sell",tower))
    popUpButtons.append(Button(Rect(x-50,y-75,45,45),None,"up dmg",tower))
    popUpButtons.append(Button(Rect(x,y-75,45,45),None,"up fire rate",tower))
    popUpButtons.append(Button(Rect(x+50,y-75,45,45),None,"up range",tower))
    popUpButtons.append(Button(Rect(x+95,y-135,10,10),None,"quit",tower))
    popUpButtons.append(Button(Rect(x-100,y-125,45,45),None,"change priority",tower))
    popUpButtons[-2].colour=(255,0,0)
def drawCost(value,x,y):
    size=15
    costFont = pygame.font.Font("Fonts/Robot Crush.otf",size)
    costText=costFont.render("£"+str(value),True,(255,215,0))
    while costText.get_width()>34:
        size-=1
        costFont = pygame.font.Font("Fonts/Robot Crush.otf",size)
        costText=costFont.render("£"+str(value),True,(255,215,0))
    screen.blit(costText,(x+70-costText.get_width()/2,y-148))
def drawVal(value,x,y):
    valFont = pygame.font.Font("Fonts/Robot Crush.otf",15)
    valText=valFont.render(str(value),True,(100,100,100))
    screen.blit(valText,(x+20-valText.get_width()/2,y-148))
def drawPopUpMenu():
    global popUpButtons, showPopUpMenu
    if showPopUpMenu:
        x=popUpButtons[0].rect.left+100
        y=popUpButtons[0].rect.top+75
        pygame.draw.circle(screen,(0,0,0),(popUpButtons[0].tower.x,popUpButtons[0].tower.y),popUpButtons[0].tower.range,1)
        towerFont = pygame.font.Font("Fonts/Robot Crush.otf",15)
        towerText=towerFont.render(popUpButtons[0].tower.name,True,(0,0,0))
        screen.blit(towerText,(popUpButtons[0].tower.x-103,popUpButtons[0].tower.y-148))
        pygame.draw.rect(screen,(150,150,150),(x-105,y-130,205,105),0)
        pygame.draw.rect(screen,(100,100,100),(x-107,y-132,209,109),3)
        pygame.draw.rect(screen,(100,100,100),(x+53,y-155,34,22),0)#PRICE
        #pygame.draw.rect(screen,(150,150,150),(x+56,y-152,28,22),0)#PRICE
        #pygame.draw.rect(screen,(230,230,230),(x+58,y-150,24,19),0)#PRICE
        pygame.draw.rect(screen,(100,100,100),(x-7,y-155,54,22),0)#VAL
        pygame.draw.rect(screen,(150,150,150),(x-4,y-152,48,22),0)#VAL
        pygame.draw.rect(screen,(230,230,230),(x-2,y-150,44,19),0)#VAL
        popFont = pygame.font.Font("Fonts/Robot Crush.otf",15)
        smallPopFont = pygame.font.Font("Fonts/Robot Crush.otf",10)
        for button in popUpButtons:
            if button.title=="up dmg":    
                if button.tower.DMGLVL<len(button.tower.type.DMGLVLS):
                    if button.rect.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(screen,(255,255,153),button.rect,0)
                        drawCost(button.tower.type.DMGLVLS[button.tower.DMGLVL][1],x,y)
                        drawVal(button.tower.type.DMGLVLS[button.tower.DMGLVL][0],x,y)
                    else:
                        pygame.draw.rect(screen,button.colour,button.rect,0)
                    if gold>button.tower.type.DMGLVLS[button.tower.DMGLVL][1]:
                        pygame.draw.rect(screen,(0,255,0),button.rect,2)
                    else:
                        pygame.draw.rect(screen,(255,0,0),button.rect,2)
                else:
                    if button.rect.collidepoint(pygame.mouse.get_pos()):
                        drawVal(button.tower.type.DMGLVLS[button.tower.DMGLVL-1][0],x,y)
            
            elif button.title=="up fire rate":    
                if button.tower.FiRaLVL<len(button.tower.type.FiRaLVLS):
                    if button.rect.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(screen,(255,255,153),button.rect,0)
                        drawCost(button.tower.type.FiRaLVLS[button.tower.FiRaLVL][1],x,y)
                        drawVal(button.tower.type.FiRaLVLS[button.tower.FiRaLVL][0],x,y)
                    else:
                        pygame.draw.rect(screen,button.colour,button.rect,0)
                    if gold>button.tower.type.FiRaLVLS[button.tower.FiRaLVL][1]:
                        pygame.draw.rect(screen,(0,255,0),button.rect,2)
                    else:
                        pygame.draw.rect(screen,(255,0,0),button.rect,2)
                else:
                    if button.rect.collidepoint(pygame.mouse.get_pos()):
                        drawVal(button.tower.type.FiRaLVLS[button.tower.FiRaLVL-1][0],x,y)
            elif button.title=="up range":
                if button.tower.RaLVL<len(button.tower.type.RaLVLS):
                    if button.rect.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(screen,(255,255,153),button.rect,0)
                        drawCost(button.tower.type.RaLVLS[button.tower.RaLVL][1],x,y)
                        drawVal(button.tower.type.RaLVLS[button.tower.RaLVL][0],x,y)
                    else:
                        pygame.draw.rect(screen,button.colour,button.rect,0)
                    if gold>button.tower.type.RaLVLS[button.tower.RaLVL][1]:
                        pygame.draw.rect(screen,(0,255,0),button.rect,2)
                    else:
                        pygame.draw.rect(screen,(255,0,0),button.rect,2)
                else:
                    if button.rect.collidepoint(pygame.mouse.get_pos()):
                        drawVal(button.tower.type.RaLVLS[button.tower.RaLVL-1][0],x,y)
            elif button.title=="change priority":
                if button.rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen,(255,255,153),button.rect,0)
                else:
                    pygame.draw.rect(screen,button.colour,button.rect,0)
            else:
                if button.rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen,(255,255,153),button.rect,0)
                else:
                    pygame.draw.rect(screen,button.colour,button.rect,0)
            if button.tower.targetPref==0:
                prefText="Front"
            elif button.tower.targetPref==1:
                prefText="Back"
            elif button.tower.targetPref==2:
                prefText="Big"
            elif button.tower.targetPref==3:
                prefText="Small"
            priorityText=popFont.render(prefText,True,(0,0,0))
        popText1=popFont.render("Sell",True,(0,0,0))
        popText2=popFont.render("DMG",True,(0,0,0))
        DMGLVLText=popFont.render(str(button.tower.DMGLVL),True,(0,0,0))
        popText3=popFont.render("FiRa",True,(0,0,0))
        FiRaLVLText=popFont.render(str(button.tower.FiRaLVL),True,(0,0,0))
        popText4=popFont.render("Ra",True,(0,0,0))
        RaLVLText=popFont.render(str(button.tower.RaLVL),True,(0,0,0))
        targetsText=smallPopFont.render("targets:",True,(0,0,0))
        screen.blit(popText1,(x-95,y-60))
        screen.blit(popText2,(x-41,y-70))
        screen.blit(popText3,(x+5,y-70))
        screen.blit(popText4,(x+55,y-70))
        screen.blit(targetsText,(x-97,y-122))
        screen.blit(DMGLVLText,(x-30,y-50))
        screen.blit(FiRaLVLText,(x+15,y-50))
        screen.blit(RaLVLText,(x+65,y-50))
        screen.blit(priorityText,(x-78-priorityText.get_width()/2,y-107))
        
def drawStartMessage():
    messageFont = pygame.font.Font("Fonts/Robot Crush.otf",25)
    messageText=messageFont.render("When you're ready "+playerName+", hit space to start",True,(0,0,0))
    screen.blit(messageText,((screenW-200)/2-messageText.get_width()/2,10))
def drawLogo(num):
    if num==0:
        logoImage=pygame.image.load("logo.png")
    elif num==1:
        logoImage=pygame.image.load("altlogo.png")
    if gameState!="menu":
        screen.blit(logoImage,(800,0))
    else:
        screen.blit(logoImage,(400,25))
    
def checkValidPos(x,y):
    global screen
    try:
        if screen.get_at((x-10,y)) not in coloursToAvoid:
            if screen.get_at((x,y-10)) not in coloursToAvoid:
                if screen.get_at((x+10,y)) not in coloursToAvoid:
                    if screen.get_at((x,y+10)) not in coloursToAvoid:
                        if x>10:
                            if x<790:
                                if y>10:
                                    if y<790:
                                        return True
    except:
        return False
    
def checkPopUpClose():
    global showPopUpMenu
    if showPopUpMenu:
        x=popUpButtons[0].rect.left+100
        y=popUpButtons[0].rect.top+75
        if distance(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1],x,y)>170 or pygame.mouse.get_pos()[1]>y+20:
            showPopUpMenu=False
def restartGame():
    global towers, enemies, gameState, time, path, lives, score, gold, maps, currentMap, fadeout, map1waves
    towers=[]
    enemies=[]
    time=0
    lives=200
    score=0
    gold=450
    points=[(i*80,random.randint(100,screenH-100)) for i in range(11)]
    spos=random.randint(100,screenH-100)
    epos=random.randint(100,screenH-100)
    points[0]=(-20,spos)
    points[1]=(80,spos)
    points[-2]=(screenW-280,epos)
    points[-1]=(screenW-210,epos)
    path=Path(points)
    maps=[]
    maps.append(Map(path,waves))
    createBackground(maps[currentMap])
    fadeout=False
    if gameState=="over":
        pygame.mixer.music.stop()
    pygame.mixer.music.set_volume(0.3)
    gameState="placing"
def playDeathSound():
    global sounds
    #sounds.append([60,60,10,0])
num=100
def playFireSound(towerType):
##    global sounds, num
##    if num<127:
##        num+=1
##    else:
##        num=100
##    print(num)#53
    if towerType=="normie":
        sounds.append([random.randint(40,50),47,5,0,1])
    elif towerType=="back burner":
        sounds.append([random.randint(45,55),85,5,0,2])
    elif towerType=="sniper":
        sounds.append([random.randint(40,50),127,5,0,3])
    elif towerType=="freezer":
        sounds.append([random.randint(40,50),97,1,0,4])
    elif towerType=="glue gun":
        sounds.append([random.randint(40,50),53,1,0,5])
    elif towerType=="machine gun":
        sounds.append([random.randint(55,65),34,1,0,5])
    elif towerType=="bomb shooter":
        sounds.append([random.randint(40,50),116,1,0,6])
    elif towerType=="tesla cannon":
        sounds.append([random.randint(30,40),30,10,0,6])
def playBuySound(tier,tiers):
    global sounds
    freq=30+int((tier/tiers)*45)
    #freq=30+tier*10
    sounds.append([freq,11,5,0,15])
def playRejectSound():
    global sounds
    sounds.append([40,67,5,0,15])
def playClickSound():
    global sounds
    sounds.append([random.randint(40,70),115,5,0,15])
def handleSounds():
    global sounds, player
    toRemove=[]
    for sound in sounds:
        if sound[3]==0:
            player.set_instrument(sound[1],sound[4])
            player.note_on(sound[0],127,sound[4])
        if sound[3]<sound[2]:
            sound[3]+=1
        else:
            player.set_instrument(sound[1],sound[4])
            player.note_off(sound[0],127,sound[4])
            toRemove.append(sound)
            
    for item in toRemove:
        sounds.remove(item)
def checkMusic():
    global currentSong
    if not pygame.mixer.music.get_busy():
        choice=random.randint(0,6)
        while choice == currentSong:
            choice=random.randint(0,6)
        currentSong=choice
        if gameState=="over":
            pygame.mixer.music.set_volume(1)
            currentSong=10
        pygame.mixer.music.load("Copyrighted Music/"+str(currentSong)+".mp3")
        pygame.mixer.music.play()
def handleRank(playerData,addplayerbool):
    #name, score, time, gold, towers, favtower
    global playerRank
    lb=open("lb.txt","r")
    data=lb.readlines()
    lb.close()
    allData=[]
    for item in data:
        line=item.split(",")
        if len(line)>1:
            line[1]=int(line[1])
            allData.append(line)
    if addplayerbool and playerData != None:
        allData.append(playerData)
        allData=sorted(allData,key=itemgetter(1),reverse=True)
        lb=open("lb.txt","w")
        for j in range(len(allData)):
            string=""
            for i in range(len(allData[j])):
                string+=str(allData[j][i])+","
            string=string[:-1]
            if allData[j]==playerData:
                string+="\n"
            lb.write(string)
        for i in range(len(allData)):
            if allData[i]==playerData:
                playerRank=i+1
        lb.close()
    return allData
        
    
def makePlayerData():
    global gold, score, time, playerName, playerData, enemiesKilled
    typeCount=[[i,0] for i in range(len(towerTypes))]
    for tower in towers:
        for i in range(len(towerTypes)):
            if tower.type ==towerTypes[i]:
                typeCount[i][1]+=1
                break
    typeCount=sorted(typeCount,key=itemgetter(1),reverse=True)
    if typeCount[0][1] ==0:
        favTower="None"
    else:
        favTower=towerTypes[typeCount[0][0]].name
    playerData=[playerName,int(score*(1+time/1000000)),time,gold,len(towers),favTower,enemiesKilled]
def drawLeaderBoard(allData,xoff,yoff,fontsize,items):
    if fontsize==None:
        fontsize=28
    if items==None:
        items=5
    lbstr="name | time | score | gold | towers | fav tower | kill count"
    lbFont = pygame.font.Font("Fonts/Robot Crush.otf",fontsize)
    lbText=lbFont.render(lbstr,True,(255,0,0))
    screen.blit(lbText,(400-lbText.get_width()/2+xoff,410+yoff))
    if gameState=="menulb":
        pygame.draw.rect(screen,(255,0,0),Rect(25,470+yoff,950,50*items+5),5)
    else:
        pygame.draw.rect(screen,(255,0,0),Rect(5,470+yoff,790,50*items+5),5)
    for i in range(items):
        i+=scrollPos
        try:
            time1=int((int(allData[i][2])/1000)//60)
            time2=(int(allData[i][2])/1000)%60
            if time1<10:
                time1="0"+str(time1)
            else:
                time1=str(round(time1,1))
            if time2<10:
                time2="0"+str(round(time2,2))
            else:
                time2=str(round(time2,1))
            lbstr=str(i+1)+": "+str(allData[i][0])+" - "+str(time1)+":"+str(time2)+" - "+str(allData[i][1])+" - "+str(allData[i][3])+" - "+str(allData[i][4])+" - "+str(allData[i][5])+" - "+str(allData[i][6])
            if allData[i][0]==playerName:
##                lbstr="you -> "+lbstr
                lbText=lbFont.render(lbstr,True,(218,165,32))
            else:
                lbText=lbFont.render(lbstr,True,(0,0,0))
            screen.blit(lbText,(400-lbText.get_width()/2+xoff,475+50*i+yoff-50*scrollPos))
        except:
            None
def showKeyboardInput():
    global playerName
    playerFont=pygame.font.Font("Fonts/Robot Crush.otf",50)
    playerText1=playerFont.render("enter name",True,(0,0,0))
    playerText2=playerFont.render(playerName,True,(218,165,32))
    screen.blit(playerText1,(screenW/2-playerText1.get_width()/2,300))
    screen.blit(playerText2,(screenW/2-playerText2.get_width()/2,370))
def drawMenuScreen():
    global menuButtons, buttonAccValues
    bFont=pygame.font.Font("Fonts/Robot Crush.otf",50)
    for button in menuButtons:
        if button.rect.collidepoint(pygame.mouse.get_pos()):
            if buttonAccValues[button.title][0]<=0:
                playClickSound()
            buttonAccValues[button.title][0]+=buttonAccValues[button.title][1]
            if buttonAccValues[button.title][1]>0:
                buttonAccValues[button.title][1]-=0.1
            else:
                buttonAccValues[button.title][1]=0
            if button.title=="quit":
                col=(200,0,0)
            elif button.title=="start":
                col=(0,190,0)
            else:
                col=(190,190,190)
            pygame.draw.ellipse(screen,col,Rect(button.rect.left-1*buttonAccValues[button.title][0],button.rect.top-1*buttonAccValues[button.title][0],button.rect.width+2*buttonAccValues[button.title][0],button.rect.height+2*buttonAccValues[button.title][0]),0)
        else:
            if buttonAccValues[button.title][0]>0:
                buttonAccValues[button.title][0]-=buttonAccValues[button.title][1]
                buttonAccValues[button.title][1]+=0.1
            else:
                buttonAccValues[button.title][0]=0
                buttonAccValues[button.title][1]=1.5
            col=(220,220,220)
            pygame.draw.ellipse(screen,col,Rect(button.rect.left-1*buttonAccValues[button.title][0],button.rect.top-1*buttonAccValues[button.title][0],button.rect.width+2*buttonAccValues[button.title][0],button.rect.height+2*buttonAccValues[button.title][0]),0)
        btext=bFont.render(button.title,True,(0,0,0))
        screen.blit(btext,(500-btext.get_width()/2,button.rect.top+20))
def rot_center(image, angle):
    orig_rect = image.get_rect()
    rot_image = pygame.transform.rotate(image, angle)
    rot_rect = orig_rect.copy()
    rot_rect.center = rot_image.get_rect().center
    rot_image = rot_image.subsurface(rot_rect).copy()
    return rot_image
class Wave():
    def __init__(self,burstList,delay):
        self.burstList=burstList
        self.currentBurst=0
        self.delay=delay
        self.time=0
        self.done=False
    def update(self):
        global deltaTime
        self.burstList[self.currentBurst].update()
        if self.burstList[self.currentBurst].done:
            self.time+=deltaTime
        if self.time>self.delay:
            self.time=0
            if self.currentBurst<len(self.burstList)-1:
                self.currentBurst+=1
            else:
                self.done=True
            
def updateWaves():
    global waves, currentWave
    if not waves[currentWave].done:
        waves[currentWave].update()
    else:
        if currentWave<len(waves)-1:
            currentWave+=1
        else:
            ntype=waves[currentWave].burstList[waves[currentWave].currentBurst].type
            waves.append(Wave([Burst(ntype,10,1,200,10,1000)],500))
            currentWave+=1
    
buttons=[]
popUpButtons=[]
enemies=[]
towers=[]
sounds=[]
playerData=[]
menuButtons=[]
buttonAccValues={"start":[0,0],
                 "leaderboard":[0,0],
                 "settings":[0,0],
                 "quit":[0,0],
                 "back":[0,0],
                 }
points=[(i*80,random.randint(100,screenH-100)) for i in range(11)]
spos=random.randint(100,screenH-100)
epos=random.randint(100,screenH-100)
points[0]=(-20,spos)
points[1]=(80,spos)
points[-2]=(screenW-280,epos)
points[-1]=(screenW-210,epos)
path=Path(points)

fadeSurface=pygame.Surface((800,800))
fadeSurface.set_alpha(150)
fadeSurface.fill((255,255,255))

lives=200
score=0
gold=450
enemiesKilled=0
playerRank=0
playerName=""
gameState="nameinput"
time=0
fps=60
scrollPos=0
scrollItems=0
currentWave=0
newTower=None
showPopUpMenu=False
pressing=False
fadeout=False
soundStopped=False
music=False
flipSurfaceVel=(0,-10)
flipSurfacePos=(350,250)
if random.randint(0,1):
    flipDir=-1
else:
    flipDir=1
#types of enemy

#EnemyType guide(hp,movespeed,carrier bool, number of carriers, carrier type, colour of enemy, size
ct2=EnemyType(100,4,False,None,None,(128,0,128),5,1,10)
ct1=EnemyType(500,2,True,5,ct2,(255,255,0),10,5,50)

EnemyTypes=[
EnemyType(100,2,False,None,None,(0,0,0),5,1,10),
EnemyType(50,4,False,None,None,(0,255,128),3,1,5),
EnemyType(50,200,False,None,None,(0,0,0),3,10,5),
EnemyType(200,2,False,None,None,(0,0,0),3,2,15),
EnemyType(300,1,False,None,None,(0,0,0),3,2,20),
EnemyType(2000,1,True,5,ct1,(0,0,0),15,25,200),
]
base=EnemyType(50,2,False,None,None,(random.randint(0,255),random.randint(0,255),random.randint(0,255)),3,1,5)
tier1=EnemyType(150,1.75,True,1,base,(random.randint(0,255),random.randint(0,255),random.randint(0,255)),5,2,5)
tier2=EnemyType(350,1.5,True,1,tier1,(random.randint(0,255),random.randint(0,255),random.randint(0,255)),7,4,5)
tier3=EnemyType(450,1.25,True,1,tier2,(random.randint(0,255),random.randint(0,255),random.randint(0,255)),9,8,5)
tier4=EnemyType(900,1,True,1,tier3,(random.randint(0,255),random.randint(0,255),random.randint(0,255)),11,15,5)
tier5=EnemyType(1600,1,True,2,tier4,(random.randint(0,255),random.randint(0,255),random.randint(0,255)),13,30,5)
tier6=EnemyType(3200,0.8,True,2,tier5,(random.randint(0,255),random.randint(0,255),random.randint(0,255)),15,40,5)
tier7=EnemyType(10000,0.5,True,1,tier6,(random.randint(0,255),random.randint(0,255),random.randint(0,255)),15,50,5)
baseEnemyTypes=[base,tier1,tier2,tier3,tier4,tier5,tier6,tier7]

impossible=EnemyType(100000000,5,False,None,None,(0,0,0),5,1000000000,1000000000)

#types of tower

#TowerType guide(damage,fireRate:0 is fast,range in pixels, slowing bool, freezing bool,
#burning bool, electric bool, colour of tower, target pref, name, number of targets, inital cost,
#DMG level scaling, fire rate scaling, range scaling

towerTypes=[
TowerType(20,10,100,False,False,False,False,(0,0,255),0,"Normie",1,20,[[25,10],[35,15],[50,20],[1000,2500]],[[8,20],[6,30],[4,40]],[[120,15],[140,25],[160,45]]),
TowerType(5,20,70,False,False,True,False,(254,0,0),2,"Back Burner",1,100,[[10,60],[15,95],[20,150],[50,350]],[[17,25],[14,45],[11,65],[7,85]],[[80,15],[90,25],[100,45]]),
TowerType(100,100,250,False,False,False,False,(29,50,13),2,"Sniper",1,50,[[150,10],[300,20],[500,40],[750,60],[1000,80]],[[80,20],[60,30],[40,40],[30,50],[20,65],[15,80]],[[350,10],[450,15],[600,20]]),
TowerType(10,3,80,False,False,False,False,(255,128,0),3,"Machine Gun",1,60,[[15,25],[25,30],[35,60],[50,90],[75,130]],[[2,10],[1,15],[0,20]],[[90,10],[100,15],[110,20]]),
TowerType(10,100,30,False,True,False,False,(64,224,208),3,"Freezer",0,60,[[5,10],[8,15],[12,20]],[[80,10],[60,15],[40,20]],[[40,10],[55,15],[70,20]]),
TowerType(10,20,80,True,False,False,False,(204,204,0),2,"Glue Gun",1,30,[[15,10],[22,15],[35,20]],[[30,10],[20,15],[8,20]],[[95,10],[110,15],[125,20]]),
TowerType(50,25,90,False,False,False,False,(30,30,30),2,"Bomb Shooter",1,70,[[70,10],[100,35],[150,55]],[[20,10],[13,25],[8,45]],[[100,10],[120,15],[140,20]]),
TowerType(50,50,70,False,False,False,True,(220,220,30),2,"tesla cannon",1,100,[[70,10],[90,55],[130,75],[175,135]],[[35,40],[20,65],[15,75]],[[100,10],[120,15],[140,20]]),
]

coloursToAvoid=[(65,105,225),towerTypes[0].colour,towerTypes[1].colour,towerTypes[2].colour,towerTypes[3].colour,towerTypes[4].colour,towerTypes[5].colour,towerTypes[6].colour,towerTypes[7].colour]

buttons.append(Button(Rect(810,420,90,90),towerTypes[0],towerTypes[0].name,None))
buttons.append(Button(Rect(905,420,90,90),towerTypes[1],towerTypes[1].name,None))
buttons.append(Button(Rect(810,515,90,90),towerTypes[2],towerTypes[2].name,None))
buttons.append(Button(Rect(905,515,90,90),towerTypes[3],towerTypes[3].name,None))
buttons.append(Button(Rect(810,610,90,90),towerTypes[4],towerTypes[4].name,None))
buttons.append(Button(Rect(905,610,90,90),towerTypes[5],towerTypes[5].name,None))
buttons.append(Button(Rect(810,705,90,90),towerTypes[6],towerTypes[6].name,None))
buttons.append(Button(Rect(905,705,90,90),towerTypes[7],towerTypes[7].name,None))

menuButtons.append(Button(Rect(250,200,500,100),None,"start",None))
menuButtons.append(Button(Rect(250,350,500,100),None,"leaderboard",None))
menuButtons.append(Button(Rect(250,500,500,100),None,"settings",None))
menuButtons.append(Button(Rect(250,650,500,100),None,"quit",None))
backButton=Button(Rect(400,700,200,75),None,"back",None)
currentTowerType=0
#burst syntax: enemyType,count,amt,delay,repeatNum,repeatDelay
waves=[
Wave([
Burst(base,10,1,200,4,1000),
Burst(base,20,1,100,4,1000),
Burst(base,40,1,50,4,1000),
Burst(base,80,1,25,4,1000)
],500),
Wave([
Burst(tier1,10,1,200,4,1000),
Burst(base,10,1,200,4,0),
Burst(tier1,10,1,200,4,1000),
Burst(base,10,1,200,4,0),
],500),
Wave([
Burst(tier2,10,1,200,10,1000),
],500),
Wave([
Burst(tier3,5,1,100,10,500),
Burst(tier2,10,1,100,10,500),
Burst(tier3,5,1,100,10,500),
Burst(tier2,10,1,100,10,500),
Burst(tier3,5,1,100,10,500),
Burst(tier2,10,1,100,10,500),
],500),
Wave([
Burst(tier4,5,1,100,10,500),
Burst(tier3,10,1,100,10,250),
Burst(tier2,20,1,100,10,125),
Burst(tier4,5,1,100,10,500),
Burst(tier3,10,1,100,10,250),
Burst(tier2,20,1,100,10,125),
],500),
Wave([
Burst(tier5,1,1,100,50,500),
Burst(tier5,1,1,100,50,500),
],500),
Wave([
Burst(tier5,2,1,0,10,0),
Burst(tier4,4,1,0,10,0),
Burst(tier3,8,1,0,10,0),
Burst(tier2,16,1,0,10,0),
Burst(tier1,32,1,0,10,0),
],500),
Wave([
Burst(tier6,10,1,1000,25,100),
Burst(tier6,10,1,1000,25,100),
],500),
Wave([
Burst(tier7,100,1,1000,25,100),
],500),
]

maps=[]
maps.append(Map(path,waves))
currentMap=0

createBackground(maps[currentMap])


goldAcc=1

currentTime=pygame.time.get_ticks()
songTime=0
songVolume=1

if music==True:
    currentSong=0
    pygame.mixer.init()
    pygame.mixer.music.load("Copyrighted Music/0.mp3")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play()
    
loadTick=10
c=0
pygame.mouse.set_visible(False) 
while 1:
    oldTime=currentTime
    currentTime=pygame.time.get_ticks()
    deltaTime=currentTime-oldTime
    songTime+=deltaTime
    screen.fill((255,255,255))
    if gameState!="menu" and gameState!="menulb" and gameState!="nameinput":
        screen.blit(background,(0,0))
        if pygame.mouse.get_pressed()[0]:
            if not pressing:
                checkMousePos()
        else:
            goldAcc=0
            gold=int(gold)
            popUpPressing=False
            if pressing:
                if checkValidPos(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1]):
                    placeTower(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1],newTower)
                    gold-=newTower.initialCost
                pressing=False
    if gameState=="playing":
        updateWaves()
        updateEnemies()
        updateTowers()
        updateTime()
        checkHover()
    if gameState=="placing":
        drawStartMessage()
        checkHover()
        updateTowers()
    if gameState=="nameinput":
        if c<100:
            c+=1
            screen.fill((0,0,0))
            player.note_on(c,127,1)
            pygame.draw.circle(screen,(50,50,50),(500,400),c*10+15,0)
            pygame.draw.circle(screen,(100,100,100),(500,400),c*10+10,0)
            pygame.draw.circle(screen,(150,150,150),(500,400),c*10+5,0)
            pygame.draw.circle(screen,(255,255,255),(500,400),c*10,0)
        elif not soundStopped:
            soundStopped=True
            for i in range(101):
                player.note_off(i,127,1)
        showKeyboardInput()
    if not showPopUpMenu and gameState!= "over" and gameState!="menu" and gameState!="nameinput" and gameState!="menulb":
        if pygame.mouse.get_pos()[0]>795:
            if pygame.mouse.get_pos()[1]>410:
                drawBuyMenu()
    checkPopUpClose()
    if gameState!="nameinput" and gameState!="menu" and gameState!="menulb":
        if Rect(810,10,180,80).collidepoint(pygame.mouse.get_pos()):
            drawLogo(1)
            if pygame.mouse.get_pressed()[0]:
                gold+=goldAcc
                goldAcc+=0.05
            
        else:
            drawLogo(0)
    handleSounds()
    if music==True:
        checkMusic()
    if gameState!="menu" and gameState!="nameinput" and gameState!="menulb":
        drawTimes()
        drawKillCount()
        drawLives()
        drawScore()
        drawGold()
    if not pygame.mouse.get_pressed()[0] and pressing:
        pressing=False
    if gameState=="menu":
        drawPlayerName()
        checkMousePos()
        drawLogo(0)
        drawMenuScreen()
        if flipSurfacePos[1]<screenH:
            if flipSurfaceVel[1]>2:
                flipSurface=rot_center(flipSurface,360+flipDir)
            flipSurfaceVel=(flipSurfaceVel[0],flipSurfaceVel[1]+1)
            flipSurfacePos=(flipSurfacePos[0]+flipSurfaceVel[0],flipSurfacePos[1]+flipSurfaceVel[1])
            screen.blit(flipSurface,flipSurfacePos)
    elif gameState=="menulb":
        drawPlayerName()
        drawLeaderBoard(allData,100,-200,34,8)
        bigTitleFont = pygame.font.Font("Fonts/Robot Crush.otf",75)
        subTitleFont = pygame.font.Font("Fonts/Robot Crush.otf",40)
        titleText=bigTitleFont.render("leaderboard",True,(0,0,0))
        subTitleText1=subTitleFont.render("these guys know what's up",True,(0,0,0))
        subTitleText2=subTitleFont.render("(you can scroll btw)",True,(0,0,0))
        screen.blit(titleText,(500-titleText.get_width()/2,25))
        screen.blit(subTitleText1,(500-subTitleText1.get_width()/2,100))
        screen.blit(subTitleText2,(500-subTitleText2.get_width()/2,150))
        checkMousePos()
        drawLogo(0)
    elif gameState=="playing":
        drawNewTower()
        drawEnemies()
        drawTowers()
    elif gameState=="placing":
        drawNewTower()
        drawTowers()
        drawLives()
        drawGold()
    drawPopUpMenu()
    if gameState=="over":
        if not fadeout:
            pygame.mixer.music.fadeout(3000)
            fadeout=True
            makePlayerData()
            allData=handleRank(playerData,True)
            scrollPos=playerRank-math.ceil(scrollItems/2)
            if scrollPos<0:
                scrollPos=0
        updateEnemies()
        drawEnemies()
        drawTowers()
        fadeScreen()
        drawLeaderBoard(allData,0,0,None,5)
        drawEndScreen()
    
    clock=pygame.time.Clock()
    for event in pygame.event.get():
        if event.type == QUIT:
            makePlayerData()
            if score>0:
                handleRank(playerData,True)
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if gameState=="menulb" or gameState=="over":
                if event.button == 4:
                    if scrollPos>0:
                        scrollPos-=1
                if event.button == 5:
                    if scrollPos<len(allData)-math.ceil(scrollItems/2):
                        scrollPos+=1
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                if gameState=="over":
                    pygame.mixer.music.stop()
                gameState="menu"
            if showPopUpMenu:
                if event.key == K_DELETE or event.key == K_BACKSPACE:
                    towers.remove(popUpButtons[0].tower)
                    gold+=int(popUpButtons[0].tower.totalSpent*0.8)
                    playBuySound(1,10)
                    showPopUpMenu=False
            if gameState=="placing":
                if event.key==K_SPACE:
                    gameState="playing"
            elif gameState=="playing":
                if event.key==K_SPACE:
                    createEnemies(4,EnemyTypes[2],maps[currentMap].paths)
            elif gameState=="over":
                if event.key==K_SPACE:
                    restartGame()
            elif gameState=="nameinput":
                if len(playerName)<10:
                    playClickSound()
                    if event.key==K_a:
                        playerName+="a"
                    elif event.key==K_b:
                        playerName+="b"
                    elif event.key==K_c:
                        playerName+="c"
                    elif event.key==K_d:
                        playerName+="d"
                    elif event.key==K_e:
                        playerName+="e"
                    elif event.key==K_f:
                        playerName+="f"
                    elif event.key==K_g:
                        playerName+="g"
                    elif event.key==K_h:
                        playerName+="h"
                    elif event.key==K_i:
                        playerName+="i"
                    elif event.key==K_j:
                        playerName+="j"
                    elif event.key==K_k:
                        playerName+="k"
                    elif event.key==K_l:
                        playerName+="l"
                    elif event.key==K_m:
                        playerName+="m"
                    elif event.key==K_n:
                        playerName+="n"
                    elif event.key==K_o:
                        playerName+="o"
                    elif event.key==K_p:
                        playerName+="p"
                    elif event.key==K_q:
                        playerName+="q"
                    elif event.key==K_r:
                        playerName+="r"
                    elif event.key==K_s:
                        playerName+="s"
                    elif event.key==K_t:
                        playerName+="t"
                    elif event.key==K_u:
                        playerName+="u"
                    elif event.key==K_v:
                        playerName+="v"
                    elif event.key==K_w:
                        playerName+="w"
                    elif event.key==K_x:
                        playerName+="x"
                    elif event.key==K_y:
                        playerName+="y"
                    elif event.key==K_z:
                        playerName+="z"
                    elif event.key==K_SPACE:
                        if len(playerName)>0:
                            playerName+=" "
                if event.key==K_BACKSPACE:
                    playerName=playerName[:-1]
                elif event.key==K_RETURN:
                    if len(playerName)>0:
                        for i in range(101):
                            player.note_off(i,127,1)
                        pygame.mouse.set_pos([500,340])
                        pygame.mouse.set_visible(True)
                        gameState="menu"
                        flipSurface=pygame.Surface((300,200))
                        flipSurface.fill((1,0,0))
                        flipSurface.set_colorkey((1,0,0))
                        playerFont=pygame.font.Font("Fonts/Robot Crush.otf",50)
                        playerText1=playerFont.render("enter name",True,(0,0,0))
                        playerText2=playerFont.render(playerName,True,(218,165,32))
                        flipSurface.blit(playerText1,(150-playerText1.get_width()/2,50-playerText1.get_height()/2))
                        flipSurface.blit(playerText2,(150-playerText2.get_width()/2,120-playerText2.get_height()/2))
                        sounds.append([60,115,5,0,1])
            elif event.key==K_r:
                restartGame()
            elif event.key==K_1:
                fps=1
    clock.tick(fps)
    pygame.display.update()
    pygame.display.flip()

