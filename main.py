# -*- coding: utf-8 -*-
import time
import re
import sys
# from core.run import Android
# from loguru import logger
#
# a = Android(device_id='emulator-5562', cap_method='minicap', touch_method='adbtouch')
# a = Android(device_id='192.168.50.201:5555', cap_method='minicap', touch_method='miniouch')
# logger.debug(13412)

import cv2
img1=cv2.imread('test.png')
img2=cv2.imread('test1.png')
#使用SIFT算法获取图像特征的关键点和描述符
sift=cv2.xfeatures2d.SIFT_create()
kp1,des1=sift.detectAndCompute(img1,None)
kp2,des2=sift.detectAndCompute(img2,None)

#定义FLANN匹配器
indexParams=dict(algorithm=0,trees=10)
searchParams=dict(checks=50)
flann=cv2.FlannBasedMatcher(indexParams,searchParams)
#使用KNN算法实现图像匹配，并对匹配结果排序
matches=flann.knnMatch(des1,des2,k=2)
matches=sorted(matches,key=lambda x:x[0].distance)

#去除错误匹配，0.5是系数，系数大小不同，匹配的结果页不同
goodMatches=[]
for m,n in matches:
    if m.distance<0.5*n.distance:
        goodMatches.append(m)

#获取某个点的坐标位置
#index是获取匹配结果的中位数
index=int(len(goodMatches)/2)
#queryIdx是目标图像的描述符索引
x,y=kp1[goodMatches[index].queryIdx].pt
x ,y = int(x), int(y)
#将坐标位置勾画在2.png图片上，并显示
cv2.rectangle(img1,(x,y),(x+5,y+5),(0,255,255))
cv2.imshow('baofeng',img1)
cv2.waitKey()