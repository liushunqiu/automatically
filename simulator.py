import os
import json
import subprocess
from loguru import logger
from simple_emulator import SimpleEmulator

class SimulatorController:
    def __init__(self, path=None):
        # 从配置文件读取模拟器路径
        if path is None:
            try:
                if os.path.exists('app_config.json'):
                    with open('app_config.json', 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        path = config.get('simulator_path', "D:\\Program Files\\Nox\\bin")
                else:
                    path = "D:\\Program Files\\Nox\\bin"
            except Exception as e:
                logger.error(f"读取配置文件失败: {e}")
                path = "D:\\Program Files\\Nox\\bin"  # 默认路径

        self.path = path
        # 添加adb_path属性，指向adb.exe文件
        self.adb_path = os.path.join(self.path, "adb.exe")
        logger.info(f"初始化模拟器控制器，模拟器路径: {self.path}")
        logger.info(f"ADB路径: {self.adb_path}")

        # 添加全局模拟器实例，避免重复连接
        self.emulator = SimpleEmulator(self.path)
        self.is_connected = False
    
    def execute_adb_command(self, command):
        """执行ADB命令"""
        try:
            full_command = f'"{os.path.join(self.path, "adb.exe")}" {command}'
            logger.debug(f"执行ADB命令: {full_command}")
            process = subprocess.run(
                full_command, 
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='ignore'
            )
            if process.returncode != 0:
                logger.warning(f"ADB命令返回非零状态: {process.returncode}")
                logger.warning(f"错误输出: {process.stderr}")
            return process.stdout.strip()
        except Exception as e:
            logger.error(f"执行ADB命令失败: {e}")
            return ""
    
    def check_connection(self):
        """检查ADB连接状态"""
        try:
            # 使用简化的模拟器检查连接
            return self.emulator.check_adb_connection()
        except Exception as e:
            logger.error(f"检查ADB连接失败: {e}")
            return False

    # 为兼容性保留此方法
    def check_adb_connection(self):
        """检查ADB连接状态（兼容性方法）"""
        logger.info("调用check_adb_connection方法")
        return self.check_connection()

    def ensure_connection(self):
        """确保模拟器连接可用"""
        try:
            # 使用简化模拟器的连接确保方法
            result = self.emulator.ensure_connection()
            self.is_connected = result
            return result
        except Exception as e:
            logger.error(f"确保连接失败: {e}")
            self.is_connected = False
            return False
    
    def start_simulator(self):
        """启动模拟器并连接"""
        try:
            # 使用简化模拟器启动
            connection_result = self.emulator.check_adb_connection()
            logger.info(f"启动模拟器连接结果: {connection_result}")
            return connection_result
        except Exception as e:
            logger.error(f"启动模拟器失败: {e}")
            return False
    
    def tap_screen(self, x, y):
        """模拟屏幕点击"""
        try:
            command = f'shell input tap {x} {y}'
            result = self.execute_adb_command(command)
            logger.debug(f"点击屏幕坐标 ({x}, {y}) 结果: {result}")
            return True
        except Exception as e:
            logger.error(f"点击屏幕失败: {e}")
            return False
    
    def subscription(self, user):
        """进行申购操作"""
        try:
            # 检查user是字典还是对象
            account = user.get('account') if isinstance(user, dict) else getattr(user, 'account', '')
            logger.info(f"用户 {account} 开始申购操作（使用已有连接）")

            # 使用简化模拟器进行申购
            result = self.emulator.subscription(user)
            logger.info(f"用户 {account} 申购结果: {result}")
            return result
        except Exception as e:
            logger.error(f"申购操作失败: {e}")
            # 如果出错，重置连接状态，下次会重新连接
            self.is_connected = False
            return False

    def disconnect(self):
        """断开模拟器连接"""
        try:
            if self.emulator:
                logger.info("断开模拟器连接...")
                self.emulator.disconnect()
                self.is_connected = False
                logger.info("模拟器连接已断开")
        except Exception as e:
            logger.error(f"断开连接失败: {e}")

    def __del__(self):
        """析构函数，确保连接被正确关闭"""
        self.disconnect()

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logger.add("simulator_test.log", rotation="1 MB")
    
    # 测试模拟器控制器
    simulator = SimulatorController()
    connection_result = simulator.check_connection()
    print(f"模拟器连接状态: {connection_result}")
    
    if not connection_result:
        print("尝试启动模拟器...")
        start_result = simulator.start_simulator()
        print(f"启动模拟器结果: {start_result}")
    
    # 测试点击操作
    if connection_result or start_result:
        # 简单测试点击屏幕中心
        tap_result = simulator.tap_screen(200, 400)
        print(f"点击屏幕结果: {tap_result}")