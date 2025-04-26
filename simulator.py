import subprocess
import win32gui
import win32con
import os
import time
from config import Config
from emulator import Emulator

class SimulatorController:
    def __init__(self):
        self.config = Config()
        self.simulator_path = self.config.get_simulator_path()
        self.adb_path = os.path.join(self.simulator_path, "adb.exe")
        self.nox_path = os.path.join(self.simulator_path, "Nox.exe")
        print(f"模拟器路径: {self.simulator_path}")
        print(f"ADB路径: {self.adb_path}")
        print(f"模拟器可执行文件路径: {self.nox_path}")
        
    def execute_adb_command(self, command):
        """执行ADB命令"""
        try:
            if not os.path.exists(self.adb_path):
                print(f"ADB路径不存在: {self.adb_path}")
                return None
                
            full_command = f'"{self.adb_path}" {command}'
            print(f"执行命令: {full_command}")
            result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
            print(f"命令输出: {result.stdout}")
            return result.stdout
        except Exception as e:
            print(f"执行ADB命令失败: {str(e)}")
            return None
            
    def tap_screen(self, x, y):
        """模拟屏幕点击"""
        command = f"shell input tap {x} {y}"
        return self.execute_adb_command(command)
            
    def check_adb_connection(self):
        """检查ADB连接状态"""
        try:
            if not os.path.exists(self.adb_path):
                print(f"ADB路径不存在: {self.adb_path}")
                return False
                
            # 首先检查设备列表
            result = subprocess.run(
                [self.adb_path, "devices"], 
                capture_output=True, 
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            print(f"设备列表: {result.stdout}")
            
            # 检查是否有127.0.0.1:62001设备
            if "127.0.0.1:62001" in result.stdout:
                # 尝试连接设备
                connect_cmd = subprocess.run(
                    [self.adb_path, "connect", "127.0.0.1:62001"], 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                print(f"连接命令结果: {connect_cmd.stdout}")
                
                # 再次检查设备列表
                result = subprocess.run(
                    [self.adb_path, "devices"], 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                print(f"重新检查设备列表: {result.stdout}")
                
                if "127.0.0.1:62001" in result.stdout and "device" in result.stdout:
                    print("ADB连接成功")
                    return True
            
            print("ADB连接失败")
            return False
        except Exception as e:
            print(f"检查ADB连接失败: {str(e)}")
            return False
            
    def start_simulator(self):
        """启动模拟器并显示窗口"""
        try:
            if not os.path.exists(self.nox_path):
                print(f"模拟器路径不存在: {self.nox_path}")
                return False
                
            print("正在启动模拟器...")
            # 使用引号包裹路径
            command = f'start "" "{self.nox_path}"'
            print(f"执行启动命令: {command}")
            process = subprocess.Popen(
                command,
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"模拟器进程已启动，PID: {process.pid}")
            
            # 等待模拟器窗口出现
            max_wait = 30  # 最多等待30秒
            for i in range(max_wait):
                # 检查窗口
                if self.is_simulator_window_visible():
                    print("模拟器窗口已显示")
                    return True
                    
                time.sleep(1)
                print(f"等待模拟器窗口... {i+1}/{max_wait}")
                
            print("模拟器窗口未显示")
            return False
        except Exception as e:
            print(f"启动模拟器失败: {str(e)}")
            return False
            
    def is_simulator_window_visible(self):
        """检查模拟器窗口是否可见"""
        try:
            def callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "夜神模拟器" in title:
                        print(f"找到模拟器窗口: {title}")
                        extra.append(hwnd)
                return True
                
            windows = []
            win32gui.EnumWindows(callback, windows)
            return len(windows) > 0
        except Exception as e:
            print(f"检查模拟器窗口失败: {str(e)}")
            return False
            
    def bring_simulator_to_front(self):
        """将模拟器窗口置顶"""
        try:
            # 查找夜神模拟器窗口
            def callback(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "夜神模拟器" in title:
                        # 将窗口置顶
                        win32gui.SetForegroundWindow(hwnd)
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        return False
                return True
                
            win32gui.EnumWindows(callback, None)
        except Exception as e:
            print(f"置顶模拟器窗口失败: {str(e)}")

    def subscription(self, params):
        """执行完整申购操作，直接调用 Emulator 里的自动申购逻辑"""
        try:
            account = params.get('account', "")
            password = params.get('password', "")
            if not account or not password:
                print("缺少账号或密码，无法申购")
                return False

            with Emulator(self.nox_path) as emulator:
                if not emulator.device:
                    print("模拟器未连接，无法进行申购")
                    return False

                class SimpleUser:
                    def __init__(self, account, password):
                        self.account = account
                        self.password = password
                user = SimpleUser(account, password)
                emulator.subscription(user)
            return True
        except Exception as e:
            print(f"申购操作失败: {str(e)}")
            return False