# Auto_py
学习airtest

## 系统要求
python3.8


## 已完成事项
- [x] 集成minicap, javacap(airtest)
- [x] 集成minitouch, maxtouch(airtest)
- [x] 完成adb.py模块
- [x] darknet-yolov4识别
- [x] SIFT特征点匹配
- [x] ocr使用PaddleOCR
- [x] 设备旋转时的,minicap重启和坐标轴的转换
- [x] 行为树

## 待完成事项
- [ ]  surf_cuda
- [ ]  ORB_cuda

  
## 总结
- 目前截图的几种方式
  - `adb shell screencap` 保存为raw格式文件,pull到电脑,通过cv2转换为png,整体时长大约在200ms.
  - 使用minicap服务,进行socket连接
  - minicap在静态页面的获取时间额外的长
  - minicap页面旋转后需要重启服务 (https://testerhome.com/topics/11507)

- 目前点击的几种方式
  - 使用sendevent点击。延迟太高,必须要使用raw_shell,不然会发生错误,造成点击失败
  - 使用minitouch服务,socket传输点击,速度最快
  
- SIFT特征点获取时间太慢，应该加入SURF
- UI识别中,针对于多分辨率适配,按照我目前的经验来说,应该从高分辨率获取特征模板,在其他分辨率中
  通过缩放模板的大小,进行模板匹配(游戏引擎会根据原始图像进行缩放,一般取大的,往小的缩)。
