# Auto_py
简单点说抄airtest的

目前主要有以下部分:

* 集成了[minitouch](https://github.com/DeviceFarmer/minitouch)实时控制设备
* 集成了[minicap](https://github.com/DeviceFarmer/minicap)流式传输实时屏幕捕获数据


## 系统要求
python3.8


## 已完成事项
- [x] 集成minicap以达到最快的截图速度
- [x] 集成minitouch完成实时控制设备
- [x] 完成adb.py模块
- [x] darknet-yolov4识别
- [x] SIFT特征点匹配

## 待完成事项
- [ ]  minicap服务开启过程中,如果手机进行了旋转,截图会出现问题
- [ ]  行为树的重新构建
- [ ]  编译opencv-cudn
- [ ]  非root权限下的运行
- [ ]  ocr使用PaddleOCR
  
~~opencv使用yolov4识别 !编译不出gpu版本,CPU识别0.5秒一次,索性不要了~~
  
## 总结
- 目前截图的几种方式
  - `adb shell screencap` 保存为raw格式文件,pull到电脑,通过cv2转换为png,整体时长大约在200ms.
  - 使用minicap服务,进行socket连接
  - minicap在静态页面的获取时间额外的长

- 目前点击的几种方式
  - 使用sendevent点击。延迟太高,必须要使用raw_shell,不然会发生错误,造成点击失败
  - 使用minitouch服务,socket传输点击,速度最快
  
- SIFT特征点获取时间太慢，应该加入SURF
- UI识别中,针对于多分辨率适配,按照我目前的经验来说,对于不变的UI,应该从高分辨率获取特征模板,在其他分辨率中
  通过缩放模板的大小,进行模板匹配(游戏引擎会根据原始图像进行缩放,一般画大的,往小的缩)。
