import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QDialogButtonBox,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt # Qt.DialogCode 需要这个

class SettingsDialog(QDialog):
    """设置对话框，用于配置模拟器路径和券商APP包名"""
    def __init__(self, parent=None, path="", broker_package="com.hexin.plat.android"):
        """
        初始化 SettingsDialog。

        Args:
            parent (QWidget, optional): 父窗口。 Defaults to None.
            path (str, optional): 当前模拟器 bin 目录路径。 Defaults to "".
            broker_package (str, optional): 当前券商APP包名。 Defaults to "com.hexin.plat.android".
        """
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(500)
        self.simulator_path = path # 保存初始路径，用于比较是否更改
        self.broker_package = broker_package # 保存初始包名

        # 创建布局
        layout = QVBoxLayout(self)

        # 创建表单布局
        form_layout = QFormLayout()

        # 创建模拟器路径设置
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(self.simulator_path)
        self.path_edit.setReadOnly(True) # 路径通过浏览按钮设置
        path_layout.addWidget(self.path_edit)

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_simulator_path)
        path_layout.addWidget(self.browse_btn)

        form_layout.addRow("夜神模拟器bin目录:", path_layout)

        # 添加券商APP包名设置
        self.package_edit = QLineEdit(self.broker_package)
        form_layout.addRow("券商APP包名:", self.package_edit)

        # 添加表单布局到主布局
        layout.addLayout(form_layout)

        # 添加说明文字
        info_label = QLabel("请设置夜神模拟器bin目录的路径，该目录通常包含 adb.exe 文件。\n"
                            "正确配置后，程序才能正常连接和控制模拟器。\n\n"
                            "券商APP包名默认为同花顺(com.hexin.plat.android)，\n"
                            "如需使用其他券商APP，请修改为对应的包名。")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 添加按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                      QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept) # 接受更改
        button_box.rejected.connect(self.reject) # 取消更改
        layout.addWidget(button_box)

    def browse_simulator_path(self):
        """打开文件夹选择对话框，让用户选择模拟器bin目录"""
        # 使用 QLineEdit 当前的文本作为起始目录，如果为空则使用当前工作目录
        start_dir = self.path_edit.text() if self.path_edit.text() else os.getcwd()
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择夜神模拟器bin目录",
            start_dir,
            QFileDialog.Option.ShowDirsOnly
        )

        if folder_path:
            # 简单的检查：路径存在且包含 adb.exe (或 Nox.exe，取决于你的逻辑)
            adb_path = os.path.join(folder_path, "adb.exe")
            # nox_path = os.path.join(folder_path, "Nox.exe") # 或者检查 Nox.exe
            if os.path.exists(folder_path) and os.path.exists(adb_path):
                self.path_edit.setText(folder_path)
                # 注意：这里只是更新了编辑框的文本，最终路径在 get_simulator_path 中获取
            else:
                QMessageBox.warning(self, "无效路径",
                                    f"所选路径 '{folder_path}' 无效或不包含 adb.exe。\n"
                                    "请确保选择的是夜神模拟器的 bin 目录。")

    def get_simulator_path(self):
        """获取用户在对话框中设置的模拟器路径"""
        # 返回编辑框中的当前文本
        return self.path_edit.text()

    def get_broker_package(self):
        """获取用户在对话框中设置的券商APP包名"""
        return self.package_edit.text().strip()