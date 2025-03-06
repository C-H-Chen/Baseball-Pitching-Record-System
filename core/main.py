import numpy as np 
import cv2
import argparse
import imutils
import time
import math
import json
from collections import deque

# 影片處理:
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video",help="path to the (optional) video file")   #指令讀取影片
ap.add_argument("-b", "--buffer", type=int, default=50, help="max buffer size") #表示最多能處理的投球幀數
args = vars(ap.parse_args()) #存取引數值
cap = cv2.VideoCapture(args["video"]) #開啟影片檔

frames_count, fps, width, height, frameindex = cap.get(cv2.CAP_PROP_FRAME_COUNT), cap.get(cv2.CAP_PROP_FPS), cap.get( #得到fps 等
    cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT), cap.get(cv2.CAP_PROP_POS_FRAMES) #提取影片各屬性

#畫面大小
width = 1280
height = 720
screenw = 1280 

#偵測區域大小
point1x= screenw*(4/16)
point1y= screenw/16*9*(1/9)
point2x= screenw*(14/16)    
point2y= screenw/16*9*(7/9)
point3x= screenw*(7/16)

#各個好球分割區域的球數統計
c1 = 0
c2_plus = 0
c3 = 0
c4 = 0
c5 = 0      
c6 = 0
c7 = 0
c8 = 0
c9 = 0
percent = 0

#各個壞球分割區域的球數統計
b11 = 0
b12 = 0
b13 = 0
b14 = 0
b15 = 0 
b21 = 0
b22 = 0
b23 = 0
b24 = 0
b25 = 0
b31 = 0
b32 = 0
b41 = 0
b42 = 0

#紀錄視窗
strikezone = np.zeros((650, 400,3), np.uint8)
strikezone.fill(255)
location = ()
oldcircle = ()
index2 = 1
texthigh = 20
label = None

#滑鼠事件
drawing = False
Mouse_count = False

num = 0 #暫存幀數
pre = None #前幀
pts = deque(maxlen=args["buffer"]) #儲存投球軌跡

#計時器
framebuffer = 0 
framenumber = 0

#進壘點
center = None
pitch_location = None 
circle_location = None

#讀取OpenPose的檔案
file = ''
with open(file, 'r') as f:
    data = json.load(f)

down = 1

#好球帶的x座標
point1 = () 
point2 = ()

#好球帶的y座標
point3 = (0,int((data['people'][3]['pose_keypoints_2d'][25] + data['people'][3]['pose_keypoints_2d'][7])/2/1080*720))
point4 = (0, int(data['people'][3]['pose_keypoints_2d'][28]/1080*720))

#跳過x張frame
def skip(x):   
    i = 0
    while(i < x):
        cap.read()
        i = i + 1

#滑鼠點擊好球帶x座標，先左後右
def mouse_drawing(event, x, y, flags, params): #滑鼠事件
    global drawing, Mouse_count, down, point1, point2
    if Mouse_count == False:
        if down == 1:
            if event == cv2.EVENT_LBUTTONDOWN:
                if drawing is False:
                    #drawing = True
                    point1 = (x, y)
                    down = 2
        elif down == 2:
            if event == cv2.EVENT_LBUTTONDOWN:
                point2 = (x, y)
                down = 3
                Mouse_count = True

#判斷好球離九宮格中哪格最近
def where9(point):     
    global c1,c2_plus,c3,c4,c5,c6,c7,c8,c9,label,percent
    z1d = math.sqrt(int(math.pow(point[0]-zone1[0],2)+math.pow(point[1]-zone1[1],2)))  #計算兩點距離
    z2d = math.sqrt(int(math.pow(point[0]-zone2[0],2)+math.pow(point[1]-zone2[1],2)))
    z3d = math.sqrt(int(math.pow(point[0]-zone3[0],2)+math.pow(point[1]-zone3[1],2)))
    z4d = math.sqrt(int(math.pow(point[0]-zone4[0],2)+math.pow(point[1]-zone4[1],2)))
    z5d = math.sqrt(int(math.pow(point[0]-zone5[0],2)+math.pow(point[1]-zone5[1],2)))
    z6d = math.sqrt(int(math.pow(point[0]-zone6[0],2)+math.pow(point[1]-zone6[1],2)))
    z7d = math.sqrt(int(math.pow(point[0]-zone7[0],2)+math.pow(point[1]-zone7[1],2)))
    z8d = math.sqrt(int(math.pow(point[0]-zone8[0],2)+math.pow(point[1]-zone8[1],2)))
    z9d = math.sqrt(int(math.pow(point[0]-zone9[0],2)+math.pow(point[1]-zone9[1],2)))
    minzonedis = min(z1d, z2d, z3d, z4d, z5d, z6d, z7d, z8d, z9d)     #球座標跟九宮格哪格中心絕對距離最小，就當格數量+1

    if(minzonedis==z1d):    #如果最小的是第1格   c1(個數)+1    label+1 (用於統計 讓後面print知道這是哪格) percent(計算百分比)
        c1 = c1+1
        label = 1
        percent = c1
    if(minzonedis==z2d):
        c2_plus = c2_plus+1 #c2名稱用過了
        label = 2
        percent = c2_plus
    if(minzonedis==z3d):
        c3 = c3+1
        label = 3
        percent = c3
    if(minzonedis==z4d):
        c4 = c4+1
        label = 4
        percent = c4
    if(minzonedis==z5d):
        c5 = c5+1
        label = 5
        percent = c5
    if(minzonedis==z6d):
        c6 = c6+1
        label = 6
        percent = c6
    if(minzonedis==z7d):
        c7 = c7+1
        label = 7
        percent = c7
    if(minzonedis==z8d):
        c8 = c8+1
        label = 8
        percent = c8
    if(minzonedis==z9d):
        c9 = c9+1
        label = 9
        percent = c9

#判斷壞球來分割的哪格壞球區域最近
def whereBall(point):       
    global b11,b12,b13,b14,b15,b21,b22,b23,b24,b25,b31,b32,b41,b42,label,percent
    if(point[0] < point1[0]) & (point[1] < point3[1]):
        b11 = b11+1
        label = '10-1-1'
        percent = b11
    if(point[0] > point1[0]) & (point[0] < ball12) & (point[1] < point3[1]):
        b12 = b12+1
        label = '10-1-2'
        percent = b12
    if(point[0] > ball12) & (point[0] < ball13) & (point[1] < point3[1]):
        b13 = b13+1
        label = '10-1-3'
        percent = b13
    if(point[0] > ball13) & (point[0] < point2[0]) & (point[1] < point3[1]):
        b14 = b14+1
        label = '10-1-4'
        percent = b14
    if(point[0] > point2[0]) & (point[1] < point3[1]):
        b15 = b15+1
        label = '10-1-5'
        percent = b15
    if(point[0] < point1[0]) & (point[1] > point4[1]):
        b21 = b21+1
        label = '10-2-1'
        percent = b21
    if(point[0] > point1[0]) & (point[0] < ball12) & (point[1] > point4[1]):
        b22 = b22+1
        label = '10-2-2'
        percent = b22
    if(point[0] > ball12) & (point[0] < ball13) & (point[1] > point4[1]):
        b23 = b23+1
        label = '10-2-3'
        percent = b23
    if(point[0] > ball13) & (point[0] < point2[0]) & (point[1] > point4[1]):
        b24 = b24+1
        label = '10-2-4'
        percent = b24
    if(point[0] > point2[0]) & (point[1] > point4[1]):
        b25 = b25+1
        label = '10-2-5'
        percent = b25
    if(point[0] < point1[0]) & (point[1] < ball34) & (point[1] > point3[1]):
        b31 = b31+1
        label = '10-3-1'
        percent = b31
    if(point[0] < point1[0]) & (point[1] > ball34) & (point[1] < point4[1]):
        b32 = b32+1
        label = '10-3-2'
        percent = b32
    if(point[0] > point2[0]) & (point[1] < ball34) & (point[1] > point3[1]):
        b41 = b41+1
        label = '10-4-1'
        percent = b41
    if(point[0] > point2[0]) & (point[1] > ball34) & (point[1] < point4[1]):
        b42 = b42+1
        label = '10-4-2'
        percent = b42

cv2.namedWindow("Ball Tracking") #創建視窗並顯示影像
cv2.setMouseCallback("Ball Tracking", mouse_drawing) #設置滑鼠事件

#影像處理與運算:
ret, prevFrame = cap.read() #先輸入第一幀
prevGray = cv2.cvtColor(prevFrame, cv2.COLOR_BGR2GRAY) #灰階化
pre = cv2.GaussianBlur(prevGray, (9, 9), 0) #前幀變數，高斯模糊

while True:
    ret,frame = cap.read()  #從影片讀入frame
    if frame is None:
        break

    cp = frame.copy()
    gray2 = cv2.cvtColor(cp, cv2.COLOR_BGR2GRAY) #灰階化
    gray = cv2.GaussianBlur(gray2, (9, 9), 0) #後幀變數，高斯模糊

  #影像運算，去除靜態背景
    sub = cv2.subtract(gray, pre)   #後幀-前幀
    pre = np.copy(gray) #後幀轉為前幀
    t,mask1 = cv2.threshold(sub, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)   #影像二值化

  #影像三原色處理
    b, g, r = cv2.split(cp) #各別提取R G B
    r = cv2.GaussianBlur(r, (9, 9), 0)
    b = cv2.GaussianBlur(b, (9, 9), 0)
    g = cv2.GaussianBlur(g, (9, 9), 0)

  #閾值處理，cv2.THRESH_OTSU會自動計算出最佳閾值
    retval, r = cv2.threshold(r, 0, 255, cv2.THRESH_OTSU)
    retval, g = cv2.threshold(g, 0, 255, cv2.THRESH_OTSU)
    retval, b = cv2.threshold(b, 0, 255, cv2.THRESH_OTSU)

  #基於投球時棒球的不同特性，邏輯運算所有不同結果的交集區域，最終只有符合所有條件的像素才會被保留
    mask2 = cv2.bitwise_and(b,g)    #交集
    mask3 = cv2.bitwise_and(mask2,r)
    mask = cv2.bitwise_and(mask1,mask3)

    frame = imutils.resize(frame, width=screenw) #調整影像視窗大小

  #視覺化好球帶
    if point1 and point2 and point3 and point4: 
        cv2.line(frame,  ( 0, point3[1] ) ,  ( 2000, point3[1] ) , (100, 50, 200), 2)
        cv2.line(frame,  ( 0, point4[1] ) ,  ( 2000, point4[1] ) , (100, 50, 200), 2)
        cv2.line(frame,  ( point1[0], 0 ) ,  ( point1[0],1000 ) , (100, 50, 200), 2)
        cv2.line(frame,  ( point2[0], 0 ) ,  ( point2[0], 1000 ) , (100, 50, 200), 2)
        frame_ROI = frame[point3[1]:point4[1],point1[0]:point2[0]]

        if drawing is False:
      
      #形態學處理，縮和脹
            mask = cv2.erode(mask, None, iterations=1)   
            mask = cv2.dilate(mask, None, iterations=1)

            mask = imutils.resize(mask, width=screenw)
            cv2.imshow("mask", mask) #顯示處理後的影像

      #輪廓處理
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) #搜尋輪廓
            cnts = imutils.grab_contours(cnts) #抓取輪廓
            cv2.drawContours(cp, cnts, -1, (255,0,0), 1) #繪製輪廓

            if (len(cnts)>0):
                cv2.line(frame,  ( point1[0], point3[1]+int((point4[1]-point3[1])/3) ) ,  ( point2[0], point3[1]+int((point4[1]-point3[1])/3)) , (0, 0, 255), 1)    #分割九宮格
                cv2.line(frame,  ( point1[0], point3[1]+int((point4[1]-point3[1])/3*2) ) ,  ( point2[0], point3[1]+int((point4[1]-point3[1])/3*2)) , (0, 0, 255), 1)
                cv2.line(frame,  ( point1[0]+int((point2[0]-point1[0])/3), point3[1]) ,  ( point1[0]+int((point2[0]-point1[0])/3), point4[1]) , (0, 0, 255), 1)
                cv2.line(frame,  ( point1[0]+int((point2[0]-point1[0])/3*2), point3[1]) ,  ( point1[0]+int((point2[0]-point1[0])/3*2), point4[1]) , (0, 0, 255), 1)

                tx = point2[0] - point1[0] #好球帶的寬
                ty = point4[1] - point3[1] #好球帶的高

        # 紀錄視窗的好球帶之擴展區域
                big1 = (0, point3[1])
                big2 = (tx*2, point3[1]+(ty*2))
                dx = big2[0] - big1[0]
                dy = big2[1] - big1[1]
        
        #紀錄視窗的九宮格2個座標點
                other1 = (0+100, 0+50)  
                other2 = (tx*2+100, ty*2+50)

                #視覺化記錄視窗
                cv2.rectangle(strikezone, other1, other2, (0, 0, 255), 2)    #畫紀錄視窗的九宮格
                cv2.line(strikezone,  ( other1[0], other1[1]+int((other2[1]-other1[1])/3) ) ,  ( other2[0], other1[1]+int((other2[1]-other1[1])/3)) , (0, 0, 255), 1)   #分割紀錄視窗的九宮格
                cv2.line(strikezone,  ( other1[0], other1[1]+int((other2[1]-other1[1])/3*2) ) ,  ( other2[0], other1[1]+int((other2[1]-other1[1])/3*2)) , (0, 0, 255), 1)
                cv2.line(strikezone,  ( other1[0]+int((other2[0]-other1[0])/3), other1[1]) ,  ( other1[0]+int((other2[0]-other1[0])/3), other2[1]) , (0, 0, 255), 1)
                cv2.line(strikezone,  ( other1[0]+int((other2[0]-other1[0])/3*2), other1[1]) ,  ( other1[0]+int((other2[0]-other1[0])/3*2), other2[1]) , (0, 0, 255), 1)

                cv2.putText(strikezone,'1', (other1[0]+10,other1[1]+20 ), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.putText(strikezone,'2', (other1[0]+10+int((dx/3)),other1[1]+20 ), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.putText(strikezone,'3', (other1[0]+10+int((dx/3*2)),other1[1]+20 ), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.putText(strikezone,'4', (other1[0]+10,other1[1]+20+int((dy/3)) ), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.putText(strikezone,'5', (other1[0]+10+int((dx/3)),other1[1]+20+int((dy/3)) ), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.putText(strikezone,'6', (other1[0]+10+int(dx/3*2),other1[1]+20+int(dy/3) ), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.putText(strikezone,'7', (other1[0]+10,other1[1]+20+int(dy/3*2) ), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.putText(strikezone,'8', (other1[0]+10+int(dx/3),other1[1]+20+int(dy/3*2) ), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.putText(strikezone,'9', (other1[0]+10+int(dx/3*2),other1[1]+20+int(dy/3*2) ), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 1, cv2.LINE_AA)

                cv2.putText(strikezone,'Ball',(3,140),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,0),1,cv2.LINE_AA)
                cv2.putText(strikezone,"Strike",(3,100),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,0),1,cv2.LINE_AA)
                cv2.putText(strikezone,"past",(3,180),cv2.FONT_HERSHEY_SIMPLEX,0.5,(0,0,0),1,cv2.LINE_AA)
                cv2.circle(strikezone, (20,155) ,7, (0, 128, 0), 2)
                cv2.circle(strikezone, (20,115) ,7, (0, 255, 255), -1)
                cv2.circle(strikezone, (20,195), 7, (127, 127, 127), -1)

                cv2.putText(strikezone, 'Number.', (30,350), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
                cv2.putText(strikezone, 'Time', (130,350), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
                cv2.putText(strikezone, 'Strike Zone Label', (230,350), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
                cv2.line(strikezone, ( 117,350) ,  (117,620) , (127, 127, 127), 1)
                cv2.line(strikezone, ( 205,350) ,  (205,620) , (127, 127, 127), 1)
        
        #好球帶九宮格1-9格的中心點座標
                zone1 = (point1[0]+(tx/6),point3[1]+(ty/6))       
                zone2 = (point1[0]+(tx/2),point3[1]+(ty/6))
                zone3 = (point1[0]+(tx/6*5),point3[1]+(ty/6))
                zone4 = (point1[0]+(tx/6),point3[1]+(ty/2))
                zone5 = (point1[0]+(tx/2),point3[1]+(ty/2))
                zone6 = (point1[0]+(tx/6*5),point3[1]+(ty/2))
                zone7 = (point1[0]+(tx/6),point3[1]+(ty/6*5))
                zone8 = (point1[0]+(tx/2),point3[1]+(ty/6*5))
                zone9 = (point1[0]+(tx/6*5),point3[1]+(ty/6*5))
        
        #剩餘所需的壞球區域座標
                ball12 = (point1[0]+(tx/3))
                ball13 = (point1[0]+(tx/3*2))
                ball34  = (point3[1]+(ty/2))

                R2 = None #儲存圓半徑
                center2 = None
                center3 = None
                maxratio = 0

                for c2 in cnts:
                    ((x2, y2), radius) = cv2.minEnclosingCircle(c2) #最小包圍圓(圓心與半徑)
                    M = cv2.moments(c2)
                    center2 = (int(x2), int(y2))
                    carea = radius * radius * 3.14  #最小包圍圓面積
                    area = cv2.contourArea(c2)  #輪廓面積
                    ratio = area / carea    #圓比值(面積/最小包圍圓面積) 越大者越接近圓形

          #判斷是否為棒球
                    if x2<point2x and x2>point1x and y2<point2y and y2>point1y : #偵測區域

            #半徑、面積、最小包圍圓的面積與圓比值是否皆符合閥值
                        if (radius > 6.96)&(radius < 20.5)&(area > 109.5)&(area < 800)&(carea > 152)&(carea < 1300)&(ratio >= 0.47):
                            if ratio > maxratio :   #皆符合者，找最大圓比值，最大者視為棒球
                                maxratio = ratio
                                R2 = radius
                                center3 = center2

        # 更新棒球的追蹤
                if maxratio > 0:
                    if center == None:
                        center = center3

                    else :
                        distance = math.sqrt(int(math.pow(center3[0]-center[0],2)+math.pow(center3[1]-center[1],2)))    #前後幀棒球中心座標的距離
                        if (((center3[0] - center[0]) > 0) & ((center3[1] - center[1]) > -10) & (distance <= 130)) : #前後幀棒球X座標的距離、前後幀棒球Y座標的距離、前後幀棒球中心座標的距離、前後幀棒球X座標的距離
                            center = center3
                            pts.appendleft(center3) #皆符合儲存為投球軌跡的追蹤點
                            framebuffer = 0
                            radius2 = R2
                        if (((center3[0] - center[0]) < 0) | ((center3[1] - center[1]) <= -10) | (distance > 130)):
                            if (len(pts) < 3): # 如果最後的追蹤點太少則重新啟動追蹤
                                pts.clear()
                                center = None
                                framebuffer = framebuffer + 1
                            else:
                                framebuffer = framebuffer + 1
                else:
                    framebuffer = framebuffer + 1   #計時器
        
        #繪製投球軌跡
                if (len(pts) >=3):
                    for i in range(len(pts)):   
                        if pts[i] is None:
                            continue
                        cv2.circle(frame, pts[i], 10,(0, 0, 255), 2)

        #判定最後的進壘點
                if (center!=None) & (framebuffer > int(fps*0.25)) & (len(pts) >= 3):    
                    pitch_location = center
                    circle_location = pitch_location
                    framebuffer = 0
                    pts.clear()
                    center = None
        
         #畫面標記進壘點
                if (circle_location != None):   
                    if(circle_location[0]<point2x and circle_location[0]>point1x and circle_location[1]<point2y and circle_location[1]>point1y):
                        if (num < int(fps)): #確認投球移動已結束
                            pts.clear()
                            cv2.circle(frame, (int(circle_location[0]), int(circle_location[1])), 10,(255, 255, 255), -1)
                            num = num + 1
                        else:
                            num = 0
                            circle_location = None
              
        #紀錄視窗標記進壘點 判定結果
                if (pitch_location!=None) : 
                    if(pitch_location[0]<point2x and pitch_location[0]>point1x and pitch_location[1]<point2y and pitch_location[1]>point1y):

                        #好球判定
                        if((int(pitch_location[0]+radius2) >= int(point1[0])) & (int(pitch_location[0]-radius2) <= int(point2[0])) & (int(pitch_location[1]+radius2) >= int(point3[1])) & (int(pitch_location[1]-radius2) <= int(point4[1]))):  #判定好球
                            where9(pitch_location)  
                            cv2.circle(strikezone, (int(2*(pitch_location[0]-point1[0]))+100,int(2*(pitch_location[1]-point3[1]))+50) , 17, (0, 255, 255),-1)
                            cv2.putText(strikezone, str(index2), (int(2*(pitch_location[0]-point1[0]))+100-3-1,int(2*(pitch_location[1]-point3[1]))+50+5-1), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1, cv2.LINE_AA)
                            cv2.putText(strikezone, str(index2), (30+30,350+texthigh), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1, cv2.LINE_AA)
                            cv2.putText(strikezone, str(round(framenumber / fps, 1)) + ' sec', (130,350+texthigh), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1, cv2.LINE_AA)
                            cv2.putText(strikezone, 'Strike' + ' ' + '(' + 'label' + str(label) + ' : ' +str(percent) + ')', (250,350+texthigh),cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1, cv2.LINE_AA)
                            print('Strike', str(label))
                            index2 = index2 + 1
                            texthigh = texthigh + 12
                            location = (pitch_location[0], pitch_location[1])
                            oldcircle = oldcircle + location
                            i = 0
                            while(i < (len(oldcircle)-2) ): 
                                cv2.circle(strikezone, (int(2*(oldcircle[i]-point1[0]))+100,int(2*(oldcircle[i+1]-point3[1]))+50) ,17,(127,127,127),2)
                                i = i + 2
                            pitch_location= None
            
            #壞球判定
                        else:
                            whereBall(pitch_location)
                            cv2.circle(strikezone, (int(2*(pitch_location[0]-point1[0]))+100,int(2*(pitch_location[1]-point3[1]))+50) , 17, (0,128,0),2)
                            cv2.putText(strikezone, str(index2), (int(2*(pitch_location[0]-point1[0]))+100-3-1,int(2*(pitch_location[1]-point3[1]))+50+5-1), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1, cv2.LINE_AA)
                            cv2.putText(strikezone, str(index2), (30+30,350+texthigh), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1, cv2.LINE_AA)  #紀錄
                            cv2.putText(strikezone, str(round(framenumber / fps, 1)) + ' sec', (130,350+texthigh), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1, cv2.LINE_AA)
                            cv2.putText(strikezone, 'Ball' + ' ' + '(' + 'label' + str(label) + ' : ' +str(percent) + ')', (250,350+texthigh),cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,0), 1, cv2.LINE_AA)
                            print('Ball', str(label))
                            index2 = index2 + 1  #紀錄好球的編號
                            texthigh = texthigh + 12  #兩行紀錄的間格
                            location = (pitch_location[0], pitch_location[1])
                            oldcircle = oldcircle + location
                            i = 0
                            while(i < (len(oldcircle)-2) ):
                                cv2.circle(strikezone, (int(2*(oldcircle[i]-point1[0]))+100,int(2*(oldcircle[i+1]-point3[1]))+50) ,15,(127,127,127),2)
                                i = i + 2
                            pitch_location= None
    #顯示幀數和時間
        cv2.putText(frame, "Frame: " + str(framenumber) + ' / ' + str(frames_count), (7, 50), cv2.FONT_HERSHEY_SIMPLEX,.8, (0, 128, 255), 2)
        cv2.putText(frame, 'Time: ' + str(round(framenumber / fps, 1)) + ' sec / ' + str(round(frames_count / fps, 2))
+ ' sec', (7, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 128, 255), 2)
        cv2.putText(frame, str(int(fps)) + "fps", (int(screenw/10*9),700), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    #使用者提示
        cv2.putText(frame, 'press P to stop', (7,675), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        cv2.putText(frame, 'press + to skip 3 sec', (7,700), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

  #顯示影像
    cv2.imshow("Ball Tracking", frame)
    cv2.imshow("Strike Zone",strikezone)
    framenumber = framenumber + 1

  #控制播放速度
    key = cv2.waitKey(int(1000/fps)) & 0xFF

    #關閉、快轉和暫停
    if key == ord("q"): 
        break
    if key == ord("+"):
        skip(180)
        framenumber = framenumber + 180
    if key == ord('p'):
        cv2.waitKey(0)

cap.release()
cv2.destroyAllWindows()
