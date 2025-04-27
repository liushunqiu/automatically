#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time

def check_requirements():
    """检查项目依赖是否已安装"""
    try:
        import importlib
        
        # 检查必要的库
        required_modules = [
            'PyQt6',
            'uiautomator2',
            'pywin32',
            'peewee',
            'loguru'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                importlib.import_module(module)
                print(f"✓ {module} 已安装")
            except ImportError:
                missing_modules.append(module)
                print(f"✗ {module} 未安装")
        
        if missing_modules:
            print("\n需要安装以下依赖:")
            for module in missing_modules:
                print(f"  - {module}")
            
            # 询问用户是否自动安装依赖
            answer = input("\n是否自动安装缺失的依赖? (y/n): ")
            if answer.lower() == 'y':
                print("\n正在安装依赖...")
                # 尝试不同的安装方式
                try:
                    # 尝试直接安装
                    cmd = [sys.executable, '-m', 'pip', 'install'] + missing_modules
                    subprocess.run(cmd, check=True)
                except subprocess.CalledProcessError:
                    # 如果直接安装失败，尝试使用国内镜像
                    print("直接安装失败，尝试使用国内镜像...")
                    try:
                        cmd = [sys.executable, '-m', 'pip', 'install'] + missing_modules + ['-i', 'https://pypi.tuna.tsinghua.edu.cn/simple']
                        subprocess.run(cmd, check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"安装依赖失败: {e}")
                        print("请手动安装缺失的依赖后再运行程序")
                        return False
                
                print("依赖安装完成！")
            else:
                print("请手动安装缺失的依赖后再运行程序")
                return False
        
        return True
    except Exception as e:
        print(f"检查依赖时出错: {e}")
        return False

def check_configuration():
    """检查必要的配置文件是否存在"""
    # 检查app_config.json是否存在
    if not os.path.exists('app_config.json'):
        print("警告: 未找到app_config.json配置文件")
        # 创建一个默认的配置文件
        try:
            import json
            default_config = {
                "simulator_path": "D:\\Program Files\\Nox\\bin",
                "simulator_exe_path": "D:\\Program Files\\Nox\\bin\\Nox.exe",
                "broker_package": "com.hexin.plat.android",
                "coordinates": {
                    "select_x": 201,
                    "select_y": 785,
                    "subscribe_x": 332,
                    "subscribe_y": 783,
                    "confirm_x": 197,
                    "confirm_y": 916
                }
            }
            with open('app_config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print("已创建默认配置文件app_config.json，请根据需要修改")
        except Exception as e:
            print(f"创建默认配置文件失败: {e}")
            return False
    
    return True

def main():
    """主函数，检查环境并启动应用"""
    print("="*50)
    print("自动申购助手启动器")
    print("="*50)
    
    # 检查依赖
    print("\n[1/3] 检查Python依赖...")
    if not check_requirements():
        input("\n按Enter键退出...")
        return
    
    # 检查配置
    print("\n[2/3] 检查配置文件...")
    if not check_configuration():
        input("\n按Enter键退出...")
        return
    
    # 运行主程序
    print("\n[3/3] 启动主程序...")
    try:
        if os.path.exists('main.py'):
            # 使用子进程运行主程序，这样可以捕获崩溃
            process = subprocess.Popen([sys.executable, 'main.py'], 
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       text=True)
            
            # 实时输出主程序的打印信息
            for line in process.stdout:
                print(line, end='')
            
            # 等待程序结束并获取返回码
            exit_code = process.wait()
            
            # 如果程序异常退出，打印错误信息
            if exit_code != 0:
                print(f"\n主程序异常退出，退出码: {exit_code}")
                error_output = process.stderr.read()
                if error_output:
                    print("\n错误信息:")
                    print(error_output)
        else:
            print("错误: 未找到main.py文件")
    except Exception as e:
        print(f"启动主程序时出错: {e}")
    
    input("\n按Enter键退出...")

if __name__ == "__main__":
    main() 