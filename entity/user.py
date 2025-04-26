import peewee

from entity.base_model import BaseModel


# 用户类
class User(BaseModel):
    # 主键
    id = peewee.AutoField(primary_key=True)
    # 账户名
    account = peewee.CharField()
    # 密码
    password = peewee.CharField()
    # 姓名
    user_name = peewee.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 在模型初始化时检查表是否存在
        if not User.table_exists():
            super()._meta.database.create_tables([User])

    # 指定表名称
    class Meta:
        table_name = 't_user'  # 指定表名称

    # 创建用户
    @classmethod
    def create_user(cls, account, password, user_name):
        return cls.create(account=account, password=password, user_name=user_name)

    # 根据账号查询账户
    @classmethod
    def get_user_by_account(cls, account):
        return cls.select().where(User.account == account).get()

    # 获取全部用户
    @classmethod
    def get_all_user(cls):
        return cls.select()
#User.create_user(302319669271,280114,"雷国荣")
#User.delete_by_id(6)