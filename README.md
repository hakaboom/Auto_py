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
- [ ]  更加合适的行为树设计
- [ ]  基于PYQT5的图片管理软件
- [ ]  重写cv模块,增加适应于不同图片的特征点获取与匹配方法

  
## 总结
- 目前截图的几种方式
  - `adb shell screencap` 保存为raw格式文件,pull到电脑,通过cv2转换为png,整体时长大约在200ms.
  - minicap在静态页面的获取时间额外的长
  - minicap页面旋转后需要重启服务 (https://testerhome.com/topics/11507)
    - (2021/4/24) rotation.py中,通过新建一个线程,监听adb屏幕方向,动态重启服务 

- 目前点击的几种方式
  - 使用sendevent点击。延迟太高,必须要使用raw_shell,不然会发生错误,造成点击失败
  - 使用minitouch服务,socket传输点击,速度最快
  
- 特征点获取速度(不包含CUDA)
  `orb>brief>surf>akaze>sift`
  
- 识别效果
  `orb(大数量特征点)sift>surf>akaze>brisk>orb(默认)`
- **结论**：优先选择orb,并设置orb获取最小5w以上的特征点
- SIFT效果最好.SURF虽然也比较好,但是对于一些面积比较小的图像识别效果不好.cuda_surf中对于图像大小也有
限制,并且获取特征点的数量竟然比cpu_surf还少,可能需要调整参数
- akaze牺牲了一部分的精准度,但是速度比sift有明显提升
- (2021/5/19)后续打算对IMAGE基础图像类增加特征点的保存,增加复用性,同时寻找最合适的特征点获取方式
- (2021/6/18)orb可以通过修改特征点获取数量,增加识别准确度,但是相应的消耗时间也会增加
- 识别方向预期：
  - 大部分场景下UI的识别通过模板匹配即可,在启动脚本时根据设备分辨率、取图分辨率,对所有图像进行缩放,参考叉叉项目(https://github.com/hakaboom/xxframe)
  - 对于一些位置不确定的可以使用特征点匹配,优选SIFT/orb,在确定的场景下可以调整为合适的特征点获取方式。(需求:IMAGE基础图像类中可以设定默认的特征点获取方式或是优先级)
  - 可以考虑使用yolo识别,有现有darknet或者paddle去用,上手难度不会很大,但是对于训练时间,训练素材的获取时间成本还需要考虑
