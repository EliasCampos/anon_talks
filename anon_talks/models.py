from enum import Enum

from tortoise import Model, fields


class TimestampMixin:
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)


class TelegramUser(TimestampMixin, Model):

    class Status(Enum):
        IN_MENU = 'in_menu'
        WAITING_OPPONENT = 'waiting_opponent'
        IN_CONVERSATION = 'in_conversation'

    tg_user_id = fields.BigIntField(unique=True, pk=True)
    tg_chat_id = fields.BigIntField(unique=True)
    status = fields.CharEnumField(Status, default=Status.IN_MENU, max_length=30)

    def __str__(self):
        return f'TG user {self.pk}'


class Conversation(TimestampMixin, Model):
    id = fields.IntField(pk=True)
    initiator = fields.ForeignKeyField('conversations.TelegramUser', related_name='started_conversations')
    opponent = fields.ForeignKeyField('conversations.TelegramUser', related_name='joined_conversations')
    finished_at = fields.DatetimeField(null=True)

    def __str__(self):
        return f'Conversation {self.pk}'
