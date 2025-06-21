#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI启动器 - 无控制台窗口版本
使用.pyw扩展名可以在Windows上隐藏控制台窗口
"""

import sys
import os

# 确保当前目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from main import MainWindow
    
    def main():
        """主函数"""
        app = QApplication(sys.argv)
        
        # 设置应用程序属性
        app.setApplicationName("自动申购助手")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("AutoTrading")
        
        # 创建并显示主窗口
        main_win = MainWindow()
        main_win.show()
        
        # 启动事件循环
        exit_code = app.exec()
        sys.exit(exit_code)

    if __name__ == '__main__':
        main()

except ImportError as e:
    # 如果缺少依赖，显示错误对话框
    try:
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "依赖错误", 
                           f"缺少必要的依赖库:\n{str(e)}\n\n请运行 run.py 来检查和安装依赖。")
        sys.exit(1)
    except:
        # 如果连PyQt6都没有，则无法显示GUI错误
        print(f"错误: {e}")
        print("请先安装PyQt6: pip install PyQt6")
        sys.exit(1)

except Exception as e:
    # 其他错误
    try:
        app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
        QMessageBox.critical(None, "程序启动错误", 
                           f"程序启动时发生错误:\n{str(e)}")
        sys.exit(1)
    except:
        print(f"程序启动失败: {e}")
        sys.exit(1)
