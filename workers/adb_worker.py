import os
import subprocess
import time
from PyQt6.QtCore import QThread, pyqtSignal
from config import Config # 假设 Config 类在根目录的 config.py 中
from simulator import SimulatorController  # 添加这行导入

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
                # ... (省略 connect 逻辑代码, 从原 main.py 复制)
                # 检查设备
                result = subprocess.run(
                    [self.adb_path, "devices"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                self.update_signal.emit(f"设备列表: {result.stdout}")

                # 重启ADB服务器
                self.update_signal.emit("重启ADB服务器...")
                subprocess.run(
                    [self.adb_path, "kill-server"],
                    capture_output=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                time.sleep(1)
                subprocess.run(
                    [self.adb_path, "start-server"],
                    capture_output=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                time.sleep(1)

                # 连接到设备
                self.update_signal.emit("连接到模拟器地址 127.0.0.1:62001...")
                connect_result = subprocess.run(
                    [self.adb_path, "connect", "127.0.0.1:62001"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                self.update_signal.emit(f"连接结果: {connect_result.stdout}")

                # 检查结果
                time.sleep(2)
                check_result = subprocess.run(
                    [self.adb_path, "devices"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                self.update_signal.emit(f"设备列表: {check_result.stdout}")

                if "127.0.0.1:62001" in check_result.stdout and "device" in check_result.stdout:
                    self.finished_signal.emit(True, "模拟器连接成功")
                else:
                    self.finished_signal.emit(False, "模拟器连接失败")


            elif self.cmd_type == 'check':
                self.update_signal.emit("正在检查模拟器连接状态...")
                # ... (省略 check 逻辑代码, 从原 main.py 复制)
                result = subprocess.run(
                    [self.adb_path, "devices"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                self.update_signal.emit(f"设备列表: {result.stdout}")

                if "127.0.0.1:62001" in result.stdout and "device" in result.stdout:
                    self.finished_signal.emit(True, "模拟器已连接")
                else:
                    self.finished_signal.emit(False, "模拟器未连接")

            elif self.cmd_type == 'subscribe':
                self.update_signal.emit("开始全自动申购流程...")
                
                # 检查设备连接状态
                self.update_signal.emit("检查设备连接状态...")
                device_result = subprocess.run(
                    [self.adb_path, "devices"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                if "127.0.0.1:62001" not in device_result.stdout or "device" not in device_result.stdout:
                    self.update_signal.emit("设备未连接或状态异常")
                    self.finished_signal.emit(False, "设备未连接或状态异常")
                    return

                try:
                    # 使用SimulatorController替代Emulator
                    simulator = SimulatorController()
                    if not simulator.check_adb_connection():
                        self.update_signal.emit("ADB连接失败")
                        self.finished_signal.emit(False, "ADB连接失败")
                        return
                    
                    # 直接执行申购操作，不需要User对象
                    broker_package = self.params.get('broker_package', "")
                    if not broker_package:
                        config = Config()
                        broker_package = config.get_broker_package_name()
                    
                    self.update_signal.emit("开始执行申购操作...")
                    # 执行完整的申购流程
                    if simulator.subscription(self.params):
                        self.update_signal.emit("申购操作执行完成")
                        self.finished_signal.emit(True, "申购操作已完成")
                        return  # 关键修改：成功后立即返回
                    else:
                        raise Exception("申购流程执行失败")
                    
                except Exception as e:
                    self.update_signal.emit(f"执行出错: {str(e)}")
                    self.finished_signal.emit(False, f"操作失败: {str(e)}")
                    return  # 关键修改：失败后立即返回

                # 删除以下冗余代码！！！
                # 获取券商APP包名
                # config = Config()
                # broker_package = config.get_broker_package_name()

                # 获取应用列表，检查券商APP是否已安装
                self.update_signal.emit(f"检查券商APP({broker_package})是否已安装...")
                package_check = subprocess.run(
                    [self.adb_path, "shell", "pm", "list", "packages", broker_package],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )

                if broker_package not in package_check.stdout:
                    self.update_signal.emit(f"未找到券商APP({broker_package})，请确保已安装")
                    self.finished_signal.emit(False, f"未找到券商APP({broker_package})")
                    return

                # 关闭可能已经打开的券商APP
                self.update_signal.emit(f"关闭已打开的券商APP({broker_package})...")
                subprocess.run(
                    [self.adb_path, "shell", "am", "force-stop", broker_package],
                    capture_output=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                time.sleep(1)

                # 启动券商APP
                self.update_signal.emit(f"启动券商APP({broker_package})...")
                start_result = subprocess.run(
                    [self.adb_path, "shell", "monkey", "-p", broker_package, "-c", "android.intent.category.LAUNCHER", "1"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                self.update_signal.emit(f"启动APP结果: {start_result.stdout}")

                # 等待APP启动
                self.update_signal.emit("等待APP启动（8秒）...")
                time.sleep(8)

                # 关闭可能的启动广告
                self.update_signal.emit("尝试关闭启动广告...")
                subprocess.run(
                    [self.adb_path, "shell", "input", "tap", "670", "85"],  # 右上角关闭按钮
                    capture_output=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                time.sleep(1)

                # 点击交易按钮
                self.update_signal.emit("点击交易按钮...")
                subprocess.run(
                    [self.adb_path, "shell", "input", "tap", "150", "1000"],  # 底部交易按钮
                    capture_output=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                time.sleep(3)

                # 如果需要登录，输入资金账户和密码
                self.update_signal.emit("检查是否需要登录...")

                # 获取账号和密码
                account = self.params.get('account', "")
                password = self.params.get('password', "")

                if account and password:
                    self.update_signal.emit("尝试登录账户...")

                    # 点击资金账号框
                    self.update_signal.emit("点击资金账号...")
                    subprocess.run(
                        [self.adb_path, "shell", "input", "tap", "200", "300"],  # 资金账号位置
                        capture_output=True,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    time.sleep(1)

                    # 点击密码输入框
                    self.update_signal.emit("点击密码输入框...")
                    subprocess.run(
                        [self.adb_path, "shell", "input", "tap", "200", "400"],  # 密码输入框位置
                        capture_output=True,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    time.sleep(1)

                    # 输入密码（数字键盘）
                    self.update_signal.emit("输入密码...")
                    for digit in password:
                        x, y = self.get_numeric_key_position(digit)
                        subprocess.run(
                            [self.adb_path, "shell", "input", "tap", str(x), str(y)],
                            capture_output=True,
                            encoding='utf-8',
                            errors='ignore'
                        )
                        time.sleep(0.5)

                    # 点击登录按钮
                    self.update_signal.emit("点击登录按钮...")
                    subprocess.run(
                        [self.adb_path, "shell", "input", "tap", "360", "520"],  # 登录按钮位置
                        capture_output=True,
                        encoding='utf-8',
                        errors='ignore'
                    )
                    time.sleep(3)
                else:
                    self.update_signal.emit("未提供账号密码，假设已登录")

                # 点击"新股/新债申购"图标
                self.update_signal.emit("点击新股申购图标...")
                subprocess.run(
                    [self.adb_path, "shell", "input", "tap", "120", "200"],  # 新股申购图标位置
                    capture_output=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                time.sleep(3)

                # 点击全选按钮
                self.update_signal.emit("点击全选按钮...")
                select_x = self.params.get('select_x', 201)
                select_y = self.params.get('select_y', 785)
                subprocess.run(
                    [self.adb_path, "shell", "input", "tap", str(select_x), str(select_y)],
                    capture_output=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                time.sleep(1)

                # 点击申购按钮
                self.update_signal.emit("点击申购按钮...")
                subscribe_x = self.params.get('subscribe_x', 332)
                subscribe_y = self.params.get('subscribe_y', 783)
                subprocess.run(
                    [self.adb_path, "shell", "input", "tap", str(subscribe_x), str(subscribe_y)],
                    capture_output=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                time.sleep(1)

                # 点击确认按钮
                self.update_signal.emit("点击确认按钮...")
                confirm_x = self.params.get('confirm_x', 197)
                confirm_y = self.params.get('confirm_y', 916)
                subprocess.run(
                    [self.adb_path, "shell", "input", "tap", str(confirm_x), str(confirm_y)],
                    capture_output=True,
                    encoding='utf-8',
                    errors='ignore'
                )
                time.sleep(1)

                # 完成申购
                self.update_signal.emit("申购操作执行完成")
                self.finished_signal.emit(True, "申购操作已完成")

        except Exception as e:
            self.update_signal.emit(f"执行出错: {str(e)}")
            self.finished_signal.emit(False, f"操作失败: {str(e)}")