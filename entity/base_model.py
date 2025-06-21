import peewee
import os

# 数据库路径
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'mydatabase.db')

db = peewee.SqliteDatabase(db_path)

class BaseModel(peewee.Model):
    class Meta:
        database = db