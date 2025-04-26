import uiautomator2 as u2
import time
from config import Config
import os
import subprocess

class AutomationController:
    def __init__(self):
        self.config = Config()
        self.device = None
        self.connect_device()
        
    def connect_device(self):
        """连接设备"""
        try:
            # 获取ADB路径
            adb_path = os.path.join(self.config.get_simulator_path(), "adb.exe")
            
            # 等待模拟器启动
            print("等待模拟器启动...")
            max_wait = 60  # 最多等待60秒
            for i in range(max_wait):
                # 检查设备是否在线
                result = subprocess.run([adb_path, "devices"], 
                                      capture_output=True, 
                                      text=True,
                                      encoding='utf-8',
                                      errors='ignore')
                print(f"设备列表: {result.stdout}")
                
                if "127.0.0.1:62001" in result.stdout:
                    print("模拟器已启动")
                    break
                    
                time.sleep(1)
                print(f"等待模拟器启动... {i+1}/{max_wait}")
            else:
                print("模拟器启动超时")
                return False
                
            # 停止现有的ADB服务器
            subprocess.run([adb_path, "kill-server"], 
                          capture_output=True,
                          encoding='utf-8',
                          errors='ignore')
            time.sleep(1)
            
            # 启动ADB服务器
            subprocess.run([adb_path, "start-server"], 
                          capture_output=True,
                          encoding='utf-8',
                          errors='ignore')
            time.sleep(1)
            
            # 连接到设备
            connect_result = subprocess.run([adb_path, "connect", "127.0.0.1:62001"], 
                                          capture_output=True, 
                                          text=True,
                                          encoding='utf-8',
                                          errors='ignore')
            print(f"连接结果: {connect_result.stdout}")
            
            # 等待设备连接
            time.sleep(2)
            
            # 再次检查设备是否在线
            result = subprocess.run([adb_path, "devices"], 
                                  capture_output=True, 
                                  text=True,
                                  encoding='utf-8',
                                  errors='ignore')
            print(f"重新检查设备列表: {result.stdout}")
            
            if "127.0.0.1:62001" not in result.stdout:
                print("设备连接失败，请检查模拟器设置")
                return False
                
            # 初始化uiautomator2
            self.device = u2.connect()
            
            if self.device is None:
                print("连接设备失败")
                return False
                
            print("设备连接成功")
            return True
        except Exception as e:
            print(f"连接设备失败: {str(e)}")
            print("请确保：")
            print("1. 夜神模拟器已启动")
            print("2. 模拟器已开启USB调试")
            print("3. 模拟器已开启root权限")
            return False
            
    def open_broker_app(self):
        """打开券商APP"""
        try:
            if not self.device:
                if not self.connect_device():
                    return False
                    
            # 获取包名
            package_name = self.config.get_broker_package_name()
            print(f"正在打开APP: {package_name}")
            
            # 检查APP是否已安装
            if not self.device.app_info(package_name):
                print(f"APP未安装: {package_name}")
                return False
                
            # 启动APP
            self.device.app_start(package_name)
            time.sleep(5)  # 等待应用启动
            print("APP启动成功")
            return True
        except Exception as e:
            print(f"打开券商APP失败: {str(e)}")
            return False
            
    def subscribe_new_stock(self):
        """执行新股申购操作"""
        try:
            if not self.device:
                if not self.connect_device():
                    return False
                    
            # 点击新股申购按钮
            self.device(text="新股申购").click()
            time.sleep(2)
            
            # 勾选全部
            self.device(resourceId="select_all").click()
            time.sleep(1)
            
            # 点击提交按钮
            self.device(text="提交").click()
            time.sleep(2)
            
            return True
        except Exception as e:
            print(f"申购操作失败: {str(e)}")
            return False
            
    def get_subscription_number(self):
        """获取申购编号"""
        try:
            if not self.device:
                if not self.connect_device():
                    return None
                    
            # 获取当前窗口信息
            window_info = self.device.dump_hierarchy()
            
            # 使用正则表达式提取申购编号
            import re
            pattern = r"申购编号：(\d+)"
            match = re.search(pattern, window_info)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            print(f"获取申购编号失败: {str(e)}")
            return None
            
    def check_lottery_result(self):
        """检查中签结果"""
        try:
            if not self.device:
                if not self.connect_device():
                    return False
                    
            # 点击中签查询按钮
            self.device(text="中签查询").click()
            time.sleep(2)
            
            # 获取中签信息
            result = self.device.dump_hierarchy()
            return "中签" in result
        except Exception as e:
            print(f"检查中签结果失败: {str(e)}")
            return False 