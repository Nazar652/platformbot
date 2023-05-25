from peewee import *

db = SqliteDatabase("db.sqlite")


class BotModel(Model):
    bot_token = CharField()
    is_executing = BooleanField()

    class Meta:
        database = db
