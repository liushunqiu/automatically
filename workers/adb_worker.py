import os
import subprocess
import time
from PyQt6.QtCore import QThread, pyqtSignal
from config import Config # 假设 Config 类在根目录的 config.py 中
from simulator import SimulatorController  # 添加这行导入
from emulator_improved import EmulatorImproved

class AdbWorker(QThread):
    """后台ADB操作线程"""
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, adb_path, cmd_type, params=None):
        """
        初始化 AdbWorker。

        Args:
            adb_path (str): adb.exe 的路径。
            cmd_type (str): 要执行的命令类型 ('connect', 'check', 'subscribe' 等)。
            params (dict, optional): 命令所需的额外参数。 Defaults to None.
        """
        super().__init__()
        self.adb_path = adb_path
        self.cmd_type = cmd_type
        self.params = params or {}

    def get_numeric_key_position(self, digit):
        """
        获取数字键盘上数字的坐标位置。

        Args:
            digit (str): 要获取位置的数字字符。

        Returns:
            tuple: (x, y) 坐标。
        """
        positions = {
            '1': (66, 723), '2': (205, 721), '3': (328, 720),
            '4': (64, 792), '5': (201, 785), '6': (332, 783),
            '7': (66, 853), '8': (201, 846), '9': (326, 852),
            '0': (197, 916)
        }
        return positions.get(digit, (197, 916)) # 默认返回0的位置

    def run(self):
        """
        线程执行的主函数，根据 cmd_type 执行不同的 ADB 操作。
        """
        try:
            if not os.path.exists(self.adb_path):
                self.update_signal.emit(f"错误: ADB 路径不存在 ({self.adb_path})")
                self.finished_signal.emit(False, "ADB 路径无效")
                return

            if self.cmd_type == 'connect':
                self.update_signal.emit("正在连接到模拟器...")
                # 使用改进的EmulatorImproved类
                try:
                    # 创建EmulatorImproved实例
                    self.update_signal.emit("正在创建EmulatorImproved实例...")
                    emulator = EmulatorImproved(os.path.dirname(self.adb_path))
                    
                    # 执行连接操作
                    self.update_signal.emit("开始执行EmulatorImproved.check_adb_connection()...")
                    if emulator.check_adb_connection():
                        self.update_signal.emit("模拟器连接成功!")
                        self.finished_signal.emit(True, "模拟器连接成功")
                    else:
                        self.update_signal.emit("模拟器连接失败!")
                        self.finished_signal.emit(False, "模拟器连接失败")
                except Exception as e:
                    self.update_signal.emit(f"连接过程出错: {str(e)}")
                    self.finished_signal.emit(False, f"连接错误: {str(e)}")
                
                return
            elif self.cmd_type == 'check':
                self.update_signal.emit("正在检查模拟器连接状态...")
                # 使用改进的EmulatorImproved类
                try:
                    # 创建EmulatorImproved实例
                    self.update_signal.emit("正在创建EmulatorImproved实例...")
                    emulator = EmulatorImproved(os.path.dirname(self.adb_path))
                    
                    # 执行连接操作
                    self.update_signal.emit("开始执行EmulatorImproved.check_adb_connection()...")
                    if emulator.check_adb_connection():
                        self.update_signal.emit("模拟器已连接!")
                        self.finished_signal.emit(True, "模拟器已连接")
                    else:
                        self.update_signal.emit("模拟器未连接!")
                        self.finished_signal.emit(False, "模拟器未连接")
                except Exception as e:
                    self.update_signal.emit(f"检查连接时出错: {str(e)}")
                    self.finished_signal.emit(False, f"检查错误: {str(e)}")
                
                return
            elif self.cmd_type == 'subscribe':
                self.update_signal.emit("开始全自动申购流程...")
                
                # 检查设备连接状态
                self.update_signal.emit("检查设备连接状态...")
                try:
                    # 使用SimulatorController，它现在也使用EmulatorImproved
                    simulator = SimulatorController()
                    if not simulator.check_adb_connection():
                        self.update_signal.emit("ADB连接失败，尝试重新连接...")
                        connect_success = simulator.start_simulator()
                        if not connect_success:
                            self.update_signal.emit("无法连接到模拟器，请确认模拟器已启动")
                            self.finished_signal.emit(False, "无法连接到模拟器")
                            return
                    
                    # 直接执行申购操作
                    self.update_signal.emit("开始执行申购操作...")
                    
                    # 确保params是字典类型
                    if not isinstance(self.params, dict):
                        self.update_signal.emit("参数错误: 需要字典类型参数")
                        self.finished_signal.emit(False, "参数格式错误")
                        return
                        
                    # 执行完整的申购流程
                    self.update_signal.emit(f"尝试为用户 {self.params.get('account', '未知账号')} 执行申购...")
                    operation_success = simulator.subscription(self.params)
                    
                    if operation_success:
                        self.update_signal.emit("申购操作执行完成")
                        self.finished_signal.emit(True, "申购操作已完成")
                    else:
                        self.update_signal.emit("申购操作执行失败")
                        self.finished_signal.emit(False, "申购流程执行失败")
                    
                except Exception as e:
                    self.update_signal.emit(f"执行出错: {str(e)}")
                    self.finished_signal.emit(False, f"操作失败: {str(e)}")
                
                return

        except Exception as e:
            self.update_signal.emit(f"执行出错: {str(e)}")
            self.finished_signal.emit(False, f"操作失败: {str(e)}")