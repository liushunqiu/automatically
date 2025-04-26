import peewee

from entity.base_model import BaseModel
from entity.user import User


# 用户申购记录
class UserSubscriptionRecord(BaseModel):
    # 主键
    id = peewee.AutoField(primary_key=True)
    # 账户
    user = peewee.ForeignKeyField(User, backref='user_subscription_record_list')
    # 申购代码
    subscription_code = peewee.CharField()
    # 起始配号
    start_number = peewee.CharField()
    # 债券代码
    security_code = peewee.CharField(null=True)
    # 债券简称
    security_name = peewee.CharField(null=True)
    # 中签数据
    winning_number_str = peewee.CharField(null=True)
    # 中签数量
    winning_count = peewee.IntegerField(null=True)
    # 上市日期
    listed_time = peewee.DateField(null=True)
    # 是否中签已推送
    is_winning_pushed = peewee.BooleanField(null=True)
    # 是否上市已推送
    is_listed_pushed = peewee.BooleanField(null=True)
    # 是否中签
    # is_winning = peewee.BooleanField()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 在模型初始化时检查表是否存在
        if not UserSubscriptionRecord.table_exists():
            super()._meta.database.create_tables([UserSubscriptionRecord])

    # 指定表名称
    class Meta:
        table_name = 't_user_subscription_record'  # 指定正确的表名

    # 创建记录
    @classmethod
    def create_user_subscription_record(cls, user, subscription_code, start_number):
        return cls.create(user=user, subscription_code=subscription_code, start_number=start_number)

    # 根据账号查询用户申购记录
    @classmethod
    def get_subscription_records_by_user(cls, user):
        return cls.select().where(UserSubscriptionRecord.user == user)

    # 根据申购代码获取申购记录
    @classmethod
    def get_subscription_record_by_subscription_code(cls, subscription_code, user):
        return cls.select().where((UserSubscriptionRecord.subscription_code == subscription_code) & (
                UserSubscriptionRecord.user == user)).get_or_none()

    # 获取未解析的数据
    @classmethod
    def get_unresolved_data_list(cls):
        return cls.select().where(UserSubscriptionRecord.security_code.is_null())

    # 更新债券码跟名称
    @classmethod
    def update_security(cls, subscription_code, security_code, security_name):
        update_result = (cls
                         .update(security_code=security_code, security_name=security_name)
                         .where(cls.subscription_code == subscription_code))
        n = update_result.execute()  # 执行更新操作并返回受影响的行数
        return n

    @classmethod
    def update_winning_number(cls, winning_number_str, id, count):
        update_result = (cls
                         .update(winning_number_str=winning_number_str,winning_count=count)
                         .where(cls.id == id))
        n = update_result.execute()  # 执行更新操作并返回受影响的行数
        return n

    # 获取需要判断是否中签的数据
    @classmethod
    def get_judge_winning_list(cls):
        return cls.select().where((UserSubscriptionRecord.winning_number_str.is_null())
                                  & (UserSubscriptionRecord.security_code.is_null(False)))