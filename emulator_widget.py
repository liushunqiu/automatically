#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟器嵌入组件
用于在PyQt6界面中嵌入夜神模拟器窗口
"""

import time
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt
from loguru import logger

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False
    logger.warning("win32gui 未安装，无法嵌入模拟器窗口")


class EmulatorEmbedWorker(QThread):
    """模拟器嵌入工作线程"""
    window_found = pyqtSignal(int)  # 找到窗口时发出信号，传递窗口句柄
    error_occurred = pyqtSignal(str)  # 发生错误时发出信号
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.target_title = "夜神模拟器"
        
    def run(self):
        """查找模拟器窗口"""
        self.running = True
        max_attempts = 60  # 增加到60次，每次间隔1秒

        for i in range(max_attempts):
            if not self.running:
                break

            try:
                logger.info("第 {}/{} 次查找模拟器窗口...", i+1, max_attempts)
                hwnd = self.find_emulator_window()
                if hwnd:
                    logger.info("找到模拟器窗口: {}", hwnd)
                    self.window_found.emit(hwnd)
                    return

                # 每10次尝试输出一次进度
                if (i + 1) % 10 == 0:
                    logger.info("已尝试 {} 次，继续查找...", i + 1)

                time.sleep(1)

            except Exception as e:
                logger.error("查找模拟器窗口时出错: {}", str(e))
                self.error_occurred.emit(str(e))
                return

        logger.error("尝试 {} 次后仍未找到模拟器窗口", max_attempts)
        self.error_occurred.emit(f"尝试 {max_attempts} 次后仍未找到模拟器窗口")
    
    def find_emulator_window(self):
        """查找模拟器窗口句柄"""
        if not HAS_WIN32:
            return None

        all_windows = []

        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)

                # 记录所有窗口用于调试
                all_windows.append((hwnd, window_title, class_name))

                # 更精确的匹配条件 - 优先匹配主界面窗口
                # 排除阴影窗口和弹出窗口
                is_shadow_window = "DropShadow" in class_name or "Popup" in class_name

                # 主界面窗口的特征 - 优先级从高到低
                title_matches = [
                    # 最优先：夜神模拟器的Android界面窗口
                    class_name == "SnapshotWnd" and window_title == "MainWnd",

                    # 次优先：明确的主窗口
                    "NoxPlayer" in window_title and not is_shadow_window,
                    "夜神模拟器" in window_title and not is_shadow_window,
                    window_title == "Nox" and "Qt5QWindowIcon" in class_name,

                    # 第三优先：Android相关窗口
                    "Android" in window_title and not is_shadow_window,

                    # 备选：其他模拟器窗口
                    "Nox" in window_title and not is_shadow_window,
                    "雷电模拟器" in window_title and not is_shadow_window,
                    "LDPlayer" in window_title and not is_shadow_window,
                    "BlueStacks" in window_title and not is_shadow_window,

                    # 临时：如果找不到主窗口，尝试使用阴影窗口（优先级最低）
                    "Nox" in window_title and "Qt5QWindowPopupDropShadowSaveBits" in class_name
                ]

                if any(title_matches):
                    # 计算窗口优先级
                    priority = 0
                    for i, match in enumerate(title_matches):
                        if match:
                            priority = len(title_matches) - i  # 越前面优先级越高
                            break

                    logger.info("找到匹配的模拟器窗口: {} (类名: {}, 优先级: {})", window_title, class_name, priority)
                    windows.append((hwnd, priority, window_title, class_name))
            return True

        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)

        # 调试信息：打印所有可见窗口
        logger.debug("所有可见窗口:")
        for hwnd, title, class_name in all_windows:
            if title.strip():  # 只显示有标题的窗口
                logger.debug("  窗口: {} (类名: {}, 句柄: {})", title, class_name, hwnd)

        # 按优先级排序，返回优先级最高的窗口
        if windows:
            # 按优先级降序排序
            windows.sort(key=lambda x: x[1], reverse=True)
            best_window = windows[0]
            hwnd, priority, title, class_name = best_window

            logger.info("找到 {} 个模拟器窗口，选择优先级最高的: {} (优先级: {})",
                       len(windows), title, priority)

            # 记录所有找到的窗口
            for i, (_, p, t, c) in enumerate(windows):
                logger.debug("窗口 {}: {} (类名: {}, 优先级: {})", i+1, t, c, p)

            return hwnd
        else:
            logger.warning("未找到任何模拟器窗口")
            return None
    
    def stop(self):
        """停止查找"""
        self.running = False


class EmulatorWidget(QWidget):
    """模拟器嵌入组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.emulator_hwnd = None
        self.embed_worker = None
        self.setup_ui()

        # 自动启动模拟器并嵌入
        QTimer.singleShot(1000, self.auto_start_and_embed)  # 延迟1秒启动
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        layout.setSpacing(0)  # 移除间距

        # 状态标签（可点击刷新）
        self.status_label = QLabel("正在启动模拟器...")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: white;
                padding: 5px;
                font-size: 12px;
                border-bottom: 1px solid #34495e;
            }
            QLabel:hover {
                background-color: #34495e;
                cursor: pointer;
            }
        """)
        self.status_label.mousePressEvent = self.refresh_emulator_window
        layout.addWidget(self.status_label)

        # 模拟器显示区域 - 铺满整个空间
        self.emulator_frame = QFrame()
        self.emulator_frame.setFrameStyle(QFrame.Shape.NoFrame)  # 移除边框
        self.emulator_frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border: none;
            }
        """)

        # 在frame中添加提示标签
        frame_layout = QVBoxLayout(self.emulator_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        self.placeholder_label = QLabel("正在启动夜神模拟器...\n请稍候")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("""
            QLabel {
                color: #bdc3c7;
                font-size: 16px;
                background-color: transparent;
            }
            QLabel:hover {
                color: #ecf0f1;
                cursor: pointer;
            }
        """)
        # 添加点击事件
        self.placeholder_label.mousePressEvent = self.refresh_emulator_window
        frame_layout.addWidget(self.placeholder_label)

        layout.addWidget(self.emulator_frame, 1)  # 给模拟器区域最大空间

    def auto_start_and_embed(self):
        """自动启动模拟器并嵌入 - 智能方案"""
        if not HAS_WIN32:
            self.status_label.setText("模拟器嵌入功能不可用 (需要 pywin32)")
            self.placeholder_label.setText("模拟器嵌入功能需要安装 pywin32 库\n\n请运行: pip install pywin32")
            return

        self.status_label.setText("正在检查模拟器状态...")

        # 首先检查模拟器是否已经运行
        if self.is_emulator_running():
            self.status_label.setText("模拟器已运行，正在嵌入...")
            # 即使模拟器在运行，也等待一下确保窗口完全加载
            QTimer.singleShot(5000, self.start_embed_emulator)
        else:
            # 检查ADB是否可用（说明模拟器后台已启动）
            if self.check_adb_available():
                self.status_label.setText("模拟器后台运行中，正在查找界面...")
                self.placeholder_label.setText("模拟器正在加载中...\n\n✓ ADB连接已就绪\n✓ 申购功能可用\n\n正在查找主界面...")
                # ADB可用说明模拟器在启动，立即尝试恢复窗口并查找
                QTimer.singleShot(2000, self.restore_emulator_windows)  # 2秒后先恢复窗口
                QTimer.singleShot(5000, self.start_embed_emulator)  # 等待5秒
            else:
                self.status_label.setText("正在启动模拟器...")
                self.placeholder_label.setText("正在启动夜神模拟器...\n这可能需要1-2分钟时间")
                # 启动模拟器
                if self.start_emulator():
                    # 启动后等待更长时间，先恢复窗口再查找
                    QTimer.singleShot(40000, self.restore_emulator_windows)  # 40秒后先恢复窗口
                    QTimer.singleShot(45000, self.start_embed_emulator)  # 等待45秒
                else:
                    self.status_label.setText("模拟器启动失败")
                    self.placeholder_label.setText("无法启动夜神模拟器\n请检查模拟器是否正确安装")

    def is_emulator_running(self):
        """检查模拟器是否正在运行"""
        if not HAS_WIN32:
            return False

        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)

                # 使用相同的匹配逻辑
                title_matches = [
                    "夜神模拟器" in window_title,
                    "Nox" in window_title,
                    "NoxPlayer" in window_title,
                    "雷电模拟器" in window_title,
                    "LDPlayer" in window_title,
                    "BlueStacks" in window_title,
                    "Android" in window_title and "Emulator" in window_title
                ]

                if any(title_matches):
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(enum_windows_callback, windows)
        result = len(windows) > 0
        logger.info("模拟器运行检查结果: {}", "运行中" if result else "未运行")
        return result

    def check_adb_available(self):
        """检查ADB是否可用（说明模拟器后台已启动）"""
        try:
            import subprocess
            import os

            # 尝试从配置文件读取ADB路径
            adb_path = None
            try:
                import json
                if os.path.exists('app_config.json'):
                    with open('app_config.json', 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        simulator_path = config.get('simulator_path')
                        if simulator_path:
                            adb_path = os.path.join(simulator_path, 'adb.exe')
            except Exception:
                pass

            # 如果没有配置，使用默认路径
            if not adb_path or not os.path.exists(adb_path):
                possible_paths = [
                    "D:\\Program Files\\Nox\\bin\\adb.exe",
                    "C:\\Program Files\\Nox\\bin\\adb.exe",
                    "C:\\Program Files (x86)\\Nox\\bin\\adb.exe"
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        adb_path = path
                        break

            if not adb_path:
                return False

            # 检查ADB设备连接
            result = subprocess.run(
                [adb_path, 'devices'],
                capture_output=True,
                text=True,
                timeout=5
            )

            # 检查是否有设备连接
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines[1:]:  # 跳过标题行
                    if 'device' in line and 'offline' not in line:
                        logger.info("检测到ADB设备连接: {}", line.strip())
                        return True

            return False

        except Exception as e:
            logger.warning("检查ADB状态失败: {}", str(e))
            return False

    def start_emulator(self):
        """启动夜神模拟器"""
        try:
            import subprocess
            import os

            # 常见的夜神模拟器安装路径
            possible_paths = [
                "D:\\Program Files\\Nox\\bin\\Nox.exe",
                "C:\\Program Files\\Nox\\bin\\Nox.exe",
                "C:\\Program Files (x86)\\Nox\\bin\\Nox.exe",
                "D:\\Nox\\bin\\Nox.exe",
                "C:\\Nox\\bin\\Nox.exe"
            ]

            # 尝试从配置文件读取路径
            try:
                import json
                if os.path.exists('app_config.json'):
                    with open('app_config.json', 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        simulator_path = config.get('simulator_path')
                        if simulator_path:
                            nox_exe = os.path.join(simulator_path, '..', 'Nox.exe')
                            if os.path.exists(nox_exe):
                                possible_paths.insert(0, nox_exe)
            except Exception:
                pass

            # 查找并启动模拟器
            for nox_path in possible_paths:
                if os.path.exists(nox_path):
                    logger.info("启动夜神模拟器: {}", nox_path)
                    subprocess.Popen([nox_path], shell=True)
                    return True

            logger.error("未找到夜神模拟器")
            return False

        except Exception as e:
            logger.error("启动模拟器失败: {}", str(e))
            return False

    def start_embed_emulator(self):
        """开始嵌入模拟器"""
        if not HAS_WIN32:
            self.status_label.setText("模拟器嵌入功能不可用")
            self.placeholder_label.setText("模拟器嵌入功能需要安装 pywin32 库\n\n请运行: pip install pywin32")
            return

        self.status_label.setText("正在查找模拟器窗口...")

        # 启动查找线程
        self.embed_worker = EmulatorEmbedWorker()
        self.embed_worker.window_found.connect(self.on_window_found)
        self.embed_worker.error_occurred.connect(self.on_error_occurred)
        self.embed_worker.start()
        
    def on_window_found(self, hwnd):
        """找到窗口时的处理"""
        try:
            self.emulator_hwnd = hwnd

            # 检查窗口尺寸，判断是否是阴影窗口
            if HAS_WIN32:
                window_rect = win32gui.GetWindowRect(hwnd)
                width = window_rect[2] - window_rect[0]
                height = window_rect[3] - window_rect[1]

                # 如果窗口太小（可能是阴影窗口），给出特殊提示
                if width < 200 or height < 200:
                    self.embed_window(hwnd)
                    self.status_label.setText("模拟器已嵌入 (可能是阴影窗口)")
                    self.placeholder_label.setText(
                        "⚠️ 当前嵌入的可能是阴影窗口\n\n"
                        "✓ ADB连接正常，申购功能可用\n"
                        "✓ 所有自动化操作都能正常执行\n\n"
                        "如需查看完整模拟器界面：\n"
                        "1. 手动打开夜神模拟器\n"
                        "2. 点击状态栏重新尝试嵌入\n\n"
                        "💡 提示：点击状态栏可重新查找窗口"
                    )
                    self.placeholder_label.show()
                    return

            self.embed_window(hwnd)
            self.status_label.setText("模拟器已嵌入")
            self.placeholder_label.hide()

        except Exception as e:
            logger.error("嵌入窗口失败: {}", str(e))
            self.status_label.setText(f"嵌入失败: {str(e)}")

        finally:
            pass  # 按钮已移除，无需操作
            
    def on_error_occurred(self, error_msg):
        """发生错误时的处理"""
        # 检查是否是因为找不到窗口
        if "未找到模拟器窗口" in error_msg:
            # 检查ADB是否可用
            if self.check_adb_available():
                self.status_label.setText("模拟器运行中 (ADB已连接)")
                self.placeholder_label.setText(
                    "✓ 模拟器后台运行正常\n"
                    "✓ ADB连接已建立\n"
                    "✓ 申购功能完全可用\n\n"
                    "模拟器主界面可能最小化了\n"
                    "您可以直接使用左侧的申购功能\n\n"
                    "如需查看模拟器界面，\n"
                    "请手动打开夜神模拟器窗口\n\n"
                    "💡 提示：点击此状态区域可重新尝试嵌入"
                )
            else:
                self.status_label.setText("模拟器连接失败")
                self.placeholder_label.setText(
                    f"无法连接到模拟器\n\n"
                    f"错误信息: {error_msg}\n\n"
                    f"请检查:\n"
                    f"1. 夜神模拟器是否已安装\n"
                    f"2. 模拟器是否正常启动\n"
                    f"3. 防火墙是否阻止连接\n\n"
                    f"💡 提示：点击此状态区域可重新尝试"
                )
        else:
            self.status_label.setText(f"嵌入失败: {error_msg}")
            self.placeholder_label.setText(f"无法嵌入模拟器\n\n{error_msg}\n\n💡 提示：点击此状态区域可重新尝试")
        
    def embed_window(self, hwnd):
        """嵌入窗口"""
        if not HAS_WIN32:
            return

        try:
            # 首先确保模拟器窗口可见和正常状态
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # 恢复窗口（如果被最小化）
            win32gui.SetForegroundWindow(hwnd)  # 将窗口置于前台

            # 获取frame的窗口句柄
            frame_hwnd = int(self.emulator_frame.winId())

            # 设置模拟器窗口为子窗口
            win32gui.SetParent(hwnd, frame_hwnd)

            # 调整窗口样式 - 移除所有装饰
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            style = style & ~win32con.WS_CAPTION & ~win32con.WS_THICKFRAME & ~win32con.WS_BORDER
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

            # 移除扩展样式
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex_style = ex_style & ~win32con.WS_EX_CLIENTEDGE & ~win32con.WS_EX_WINDOWEDGE
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

            # 获取模拟器窗口的原始尺寸
            window_rect = win32gui.GetWindowRect(hwnd)
            original_width = window_rect[2] - window_rect[0]
            original_height = window_rect[3] - window_rect[1]

            # 获取frame的尺寸
            frame_rect = self.emulator_frame.geometry()
            frame_width = frame_rect.width()
            frame_height = frame_rect.height()

            logger.info("模拟器原始尺寸: {}x{}, Frame尺寸: {}x{}",
                       original_width, original_height, frame_width, frame_height)

            # 计算合适的缩放比例，保持宽高比
            scale_x = frame_width / original_width
            scale_y = frame_height / original_height

            # 优先填充更多空间，使用更激进的缩放策略
            scale = min(scale_x, scale_y)

            # 如果缩放后太小，尝试使用更大的缩放比例
            if scale < 0.8:  # 如果缩放比例小于0.8，尝试填充更多空间
                # 允许适度超出边界以获得更好的显示效果
                target_fill_ratio = 0.9  # 目标填充90%的空间
                scale_for_width = (frame_width * target_fill_ratio) / original_width
                scale_for_height = (frame_height * target_fill_ratio) / original_height
                scale = min(scale_for_width, scale_for_height)

            # 设置缩放范围限制
            scale = max(0.2, min(scale, 3.0))  # 允许更大的缩放范围

            # 计算缩放后的尺寸
            scaled_width = int(original_width * scale)
            scaled_height = int(original_height * scale)

            # 确保不会超出frame边界太多
            if scaled_width > frame_width * 1.1:  # 允许超出10%
                scale = (frame_width * 1.1) / original_width
                scaled_width = int(original_width * scale)
                scaled_height = int(original_height * scale)

            if scaled_height > frame_height * 1.1:  # 允许超出10%
                scale = (frame_height * 1.1) / original_height
                scaled_width = int(original_width * scale)
                scaled_height = int(original_height * scale)

            # 计算居中位置
            x_offset = max(0, (frame_width - scaled_width) // 2)
            y_offset = max(0, (frame_height - scaled_height) // 2)

            logger.info("缩放比例: {:.2f}, 缩放后尺寸: {}x{}, 偏移: ({}, {})",
                       scale, scaled_width, scaled_height, x_offset, y_offset)

            # 调整窗口大小和位置
            win32gui.SetWindowPos(hwnd, 0, x_offset, y_offset,
                                scaled_width, scaled_height,
                                win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

            # 强制重绘窗口
            win32gui.InvalidateRect(hwnd, None, True)
            win32gui.UpdateWindow(hwnd)

            # 保存窗口句柄
            self.emulator_hwnd = hwnd
            self.status_label.setText("模拟器已嵌入")

            logger.info("模拟器窗口嵌入成功")

            # 启动窗口监控，检查是否需要切换到新的主窗口
            self.start_window_monitor()

        except Exception as e:
            logger.error("嵌入窗口时出错: {}", str(e))
            raise
            
    def refresh_emulator(self):
        """刷新模拟器显示"""
        if self.emulator_hwnd and HAS_WIN32:
            try:
                # 获取模拟器窗口的原始尺寸
                window_rect = win32gui.GetWindowRect(self.emulator_hwnd)
                original_width = window_rect[2] - window_rect[0]
                original_height = window_rect[3] - window_rect[1]

                # 获取frame的尺寸
                frame_rect = self.emulator_frame.geometry()
                frame_width = frame_rect.width()
                frame_height = frame_rect.height()

                # 计算合适的缩放比例，保持宽高比
                scale_x = frame_width / original_width
                scale_y = frame_height / original_height

                # 使用改进的缩放逻辑
                scale = min(scale_x, scale_y)
                scale = max(0.3, min(scale, 2.0))  # 限制缩放范围

                # 计算缩放后的尺寸
                scaled_width = int(original_width * scale)
                scaled_height = int(original_height * scale)

                # 如果缩放后仍然太小，尝试填充更多空间
                if scaled_width < frame_width * 0.6 and scaled_height < frame_height * 0.6:
                    scale = min(frame_width / original_width, frame_height / original_height) * 0.95
                    scaled_width = int(original_width * scale)
                    scaled_height = int(original_height * scale)

                # 计算居中位置
                x_offset = max(0, (frame_width - scaled_width) // 2)
                y_offset = max(0, (frame_height - scaled_height) // 2)

                # 重新调整窗口大小和位置
                win32gui.SetWindowPos(self.emulator_hwnd, 0, x_offset, y_offset,
                                    scaled_width, scaled_height,
                                    win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED)

                # 强制重绘
                win32gui.InvalidateRect(self.emulator_hwnd, None, True)
                win32gui.UpdateWindow(self.emulator_hwnd)

                logger.debug("模拟器窗口已刷新")
            except Exception as e:
                logger.error("刷新模拟器失败: {}", str(e))

    def start_window_monitor(self):
        """启动窗口监控，定期检查是否有更好的窗口可以嵌入"""
        if hasattr(self, 'window_monitor_timer'):
            self.window_monitor_timer.stop()

        self.window_monitor_timer = QTimer()
        self.window_monitor_timer.timeout.connect(self.check_for_better_window)
        self.window_monitor_timer.start(5000)  # 每5秒检查一次

        # 10次检查后停止（50秒后）
        self.monitor_count = 0
        logger.info("启动窗口监控，将检查是否有更好的模拟器窗口")

    def check_for_better_window(self):
        """检查是否有更好的窗口可以嵌入"""
        self.monitor_count += 1
        if self.monitor_count > 10:  # 检查10次后停止
            self.window_monitor_timer.stop()
            logger.info("窗口监控结束")
            return

        try:
            # 创建临时worker来查找窗口
            temp_worker = EmulatorEmbedWorker()
            new_hwnd = temp_worker.find_emulator_window()

            if new_hwnd and new_hwnd != self.emulator_hwnd:
                # 检查新窗口是否更好（有实际内容）
                window_title = win32gui.GetWindowText(new_hwnd)
                class_name = win32gui.GetClassName(new_hwnd)
                logger.info("发现新的模拟器窗口: {} (类名: {})", window_title, class_name)

                # 如果是更好的窗口，切换嵌入
                is_better_window = (
                    # 夜神模拟器的Android界面窗口（最优先）
                    (class_name == "SnapshotWnd" and window_title == "MainWnd") or
                    # 其他模拟器主窗口
                    (("NoxPlayer" in window_title or "夜神模拟器" in window_title) and
                     "DropShadow" not in class_name and "Popup" not in class_name)
                )

                if is_better_window:
                    logger.info("发现更好的模拟器窗口，切换嵌入: {}", window_title)
                    self.embed_window(new_hwnd)
                    self.window_monitor_timer.stop()
        except Exception as e:
            logger.warning("窗口监控检查失败: {}", str(e))

    def refresh_emulator_window(self, event=None):
        """手动刷新模拟器窗口（点击状态标签触发）"""
        _ = event  # 忽略事件参数
        logger.info("用户手动刷新模拟器窗口")
        self.status_label.setText("正在重新查找模拟器窗口...")

        # 停止当前的监控
        if hasattr(self, 'window_monitor_timer'):
            self.window_monitor_timer.stop()

        # 首先尝试恢复所有可能的模拟器窗口
        self.restore_emulator_windows()

        # 重新启动嵌入过程
        QTimer.singleShot(2000, self.start_embed_emulator)

    def restore_emulator_windows(self):
        """恢复所有可能被最小化的模拟器窗口"""
        if not HAS_WIN32:
            return

        logger.info("尝试恢复被最小化的模拟器窗口...")

        def enum_windows_callback(hwnd, windows):
            if win32gui.IsWindow(hwnd):
                try:
                    window_title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)

                    # 检查是否是模拟器相关窗口
                    is_emulator_window = any([
                        "夜神模拟器" in window_title,
                        "Nox" in window_title,
                        "NoxPlayer" in window_title,
                        class_name == "SnapshotWnd",
                        "雷电模拟器" in window_title,
                        "LDPlayer" in window_title,
                        "BlueStacks" in window_title
                    ])

                    if is_emulator_window:
                        # 检查窗口状态
                        placement = win32gui.GetWindowPlacement(hwnd)
                        if placement[1] == win32con.SW_SHOWMINIMIZED:  # 窗口被最小化
                            logger.info("发现被最小化的模拟器窗口: {} ({})", window_title, class_name)
                            # 恢复窗口
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(hwnd)
                            windows.append(hwnd)
                        elif not win32gui.IsWindowVisible(hwnd):  # 窗口不可见
                            logger.info("发现隐藏的模拟器窗口: {} ({})", window_title, class_name)
                            # 显示窗口
                            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                            windows.append(hwnd)

                except Exception as e:
                    pass  # 忽略获取窗口信息失败的情况
            return True

        try:
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            if windows:
                logger.info("成功恢复了 {} 个模拟器窗口", len(windows))
            else:
                logger.info("没有找到需要恢复的模拟器窗口，尝试启动夜神模拟器主界面")
                # 尝试启动夜神模拟器主界面
                try:
                    import subprocess
                    import os

                    # 夜神模拟器主程序路径
                    possible_paths = [
                        "D:\\Program Files\\Nox\\bin\\Nox.exe",
                        "C:\\Program Files\\Nox\\bin\\Nox.exe",
                        "C:\\Program Files (x86)\\Nox\\bin\\Nox.exe"
                    ]

                    for nox_path in possible_paths:
                        if os.path.exists(nox_path):
                            logger.info("启动夜神模拟器主界面: {}", nox_path)
                            subprocess.Popen([nox_path], shell=False)
                            break
                    else:
                        logger.warning("未找到夜神模拟器主程序")

                except Exception as e:
                    logger.error("启动夜神模拟器主界面失败: {}", str(e))

        except Exception as e:
            logger.error("恢复模拟器窗口时出错: {}", str(e))
            
    def resizeEvent(self, event):
        """窗口大小改变时调整模拟器窗口"""
        super().resizeEvent(event)
        if self.emulator_hwnd and HAS_WIN32:
            QTimer.singleShot(100, self.refresh_emulator)  # 延迟刷新
            
    def closeEvent(self, event):
        """关闭时清理"""
        if self.embed_worker and self.embed_worker.isRunning():
            self.embed_worker.stop()
            self.embed_worker.wait()
        super().closeEvent(event)
