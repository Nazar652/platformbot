from peewee import *

db = SqliteDatabase("db.sqlite")


class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def get_instance(cls, *args, **kwargs):
        try:
            return cls.get(*args, **kwargs)
        except DoesNotExist:
            return False

    @classmethod
    def create_instance(cls, **query):
        return cls.create(**query)


class User(BaseModel):
    identifier = IntegerField()
    firstname = CharField()
    lastname = CharField(null=True)
    username = CharField(null=True)


class BotModel(BaseModel):
    identifier = IntegerField(null=True)
    name = CharField(null=True)
    username = CharField(null=True)
    bot_token = CharField()
    is_executing = BooleanField()
    user = ForeignKeyField(User)


class Channel(BaseModel):
    identifier = IntegerField()
    title = CharField()
    bot = ForeignKeyField(BotModel)
