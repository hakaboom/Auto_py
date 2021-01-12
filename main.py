import time
from Minicap import connect

devices = connect('emulator-5562')
devices.get_display_info()
devices.get_frame()
# MNCInstaller('emulator-5554')
# frame_data = get_stream()
# print(frame_data)
# with open("test.png", "wb") as f:
#     f.write(frame_data)