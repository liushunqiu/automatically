import sqlite3
import dbutils.pooled_db
import peewee
import os

# 创建数据库连接池
# pool = dbutils.pooled_db.PooledDB(
#     creator=sqlite3.connect,
#     maxconnections=10,
#     blocking=True,
#     setsession=[],
#     database='mydatabase.db'
# )

# 创建 Peewee 数据库对象，将连接池作为参数传递
# db = peewee.SqliteDatabase(None, check_same_thread=False)
# # 初始化数据库连接
# db.init(pool.connection())
# 数据库路径
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'mydatabase.db')

db = peewee.SqliteDatabase(db_path)

class BaseModel(peewee.Model):
    class Meta:
        database = db