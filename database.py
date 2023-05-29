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

    @classmethod
    def get_all(cls):
        return cls.select().execute()

    @classmethod
    def get_join_instance(cls, joined_model, query):
        result = cls.select().join(joined_model).where(query)
        return result


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
    user = ForeignKeyField(
        User,
        backref='bots'
    )


class ChannelSubscriber(BaseModel):
    identifier = IntegerField()
    firstname = CharField()
    lastname = CharField(null=True)
    username = CharField(null=True)


class Channel(BaseModel):
    identifier = IntegerField()
    title = CharField()
    bot = ForeignKeyField(
        BotModel,
        backref='channels'
    )
    subscribers = ManyToManyField(ChannelSubscriber)


class Post(BaseModel):
    message_id = IntegerField(null=True)
    copy_message_id = IntegerField()
    copy_chat_id = IntegerField()
    is_published = BooleanField(default=False)
    publish_date = DateTimeField(null=True)
    delete_date = DateTimeField(null=True)
    channel = ForeignKeyField(
        Channel,
        backref='posts'
    )


class CyclicPost(BaseModel):
    text = TextField()
    start_date = DateTimeField()
    cyclic_time = DateTimeField()
    buttons = TextField()
    channel = ForeignKeyField(
        Channel,
        backref='cyclicposts'
    )


class AutoSignature(BaseModel):
    text = CharField()
    post = ForeignKeyField(
        Post,
        backref='autosignatures'
    )
