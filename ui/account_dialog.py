from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFormLayout, QLineEdit, QHBoxLayout,
                             QPushButton, QDialogButtonBox, QMessageBox)
from entity.user import User # 假设 User 类在 entity/user.py 中

class AccountDialog(QDialog):
    """账号管理对话框"""
    def __init__(self, parent=None):
        """
        初始化 AccountDialog。

        Args:
            parent (QWidget, optional): 父窗口。 Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("账号管理")
        self.setMinimumSize(600, 400)

        # 创建主布局
        layout = QVBoxLayout(self)

        # 创建账号表格
        self.account_table = QTableWidget(0, 3) # 0行，3列（账号、密码、姓名）
        self.account_table.setHorizontalHeaderLabels(["资金账号", "密码", "持有人姓名"])
        self.account_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.account_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.account_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.account_table)

        # 创建账号输入表单
        form_layout = QFormLayout()

        self.account_edit = QLineEdit()
        form_layout.addRow("资金账号:", self.account_edit)

        self.password_edit = QLineEdit()
        # self.password_edit.setEchoMode(QLineEdit.EchoMode.Password) # 可选：隐藏密码
        form_layout.addRow("密码:", self.password_edit)

        self.name_edit = QLineEdit()
        form_layout.addRow("持有人姓名:", self.name_edit)

        layout.addLayout(form_layout)

        # 创建按钮布局
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("添加账号")
        self.add_btn.clicked.connect(self.add_account)
        button_layout.addWidget(self.add_btn)

        self.del_btn = QPushButton("删除选中")
        self.del_btn.clicked.connect(self.delete_account)
        button_layout.addWidget(self.del_btn)

        layout.addLayout(button_layout)

        # 添加确定/取消按钮 (这里只保留OK，因为添加/删除是即时生效的)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept) # 点击OK关闭对话框
        layout.addWidget(button_box)

        # 加载账号数据
        self.load_accounts()

    def load_accounts(self):
        """从数据库加载账号并显示在表格中"""
        try:
            # 清空表格
            self.account_table.setRowCount(0)

            # 查询所有用户
            users = User.select()

            # 添加到表格
            for user in users:
                row_position = self.account_table.rowCount()
                self.account_table.insertRow(row_position)

                self.account_table.setItem(row_position, 0, QTableWidgetItem(user.account))
                self.account_table.setItem(row_position, 1, QTableWidgetItem(user.password)) # 注意：显示密码可能不安全
                self.account_table.setItem(row_position, 2, QTableWidgetItem(user.user_name))
        except Exception as e:
            QMessageBox.critical(self, "数据库错误", f"读取账号数据失败: {str(e)}")

    def add_account(self):
        """添加新账号到数据库并刷新表格"""
        account = self.account_edit.text().strip()
        password = self.password_edit.text().strip()
        user_name = self.name_edit.text().strip()

        if not account or not password:
            QMessageBox.warning(self, "输入错误", "账号和密码不能为空")
            return

        try:
            # 检查账号是否已存在
            existing = User.select().where(User.account == account)
            if existing.exists():
                QMessageBox.warning(self, "账号已存在", f"账号 {account} 已存在，不能重复添加")
                return

            # 创建新用户
            user = User(account=account, password=password, user_name=user_name)
            user.save()

            # 刷新表格
            self.load_accounts()

            # 清空输入框
            self.account_edit.clear()
            self.password_edit.clear()
            self.name_edit.clear()

            QMessageBox.information(self, "添加成功", f"账号 {account} 添加成功")
        except Exception as e:
            QMessageBox.critical(self, "添加失败", f"添加账号失败: {str(e)}")

    def delete_account(self):
        """删除选中的账号"""
        selected_rows = self.account_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "未选择", "请先选择要删除的账号行")
            return

        # 获取选中行的账号 (确保只处理选中的第一项所在的行)
        row = selected_rows[0].row()
        account_item = self.account_table.item(row, 0)
        if not account_item:
            QMessageBox.warning(self, "错误", "无法获取选中行的账号信息")
            return
        account = account_item.text()

        # 确认删除
        reply = QMessageBox.question(self, "确认删除",
            f"确定要删除账号 {account} 吗？此操作不可恢复。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 删除用户
                deleted_rows = User.delete().where(User.account == account).execute()

                if deleted_rows > 0:
                    # 刷新表格
                    self.load_accounts()
                    QMessageBox.information(self, "删除成功", f"账号 {account} 已删除")
                else:
                     QMessageBox.warning(self, "删除失败", f"数据库中未找到账号 {account}")

            except Exception as e:
                QMessageBox.critical(self, "删除失败", f"删除账号失败: {str(e)}")