import asyncio
from datetime import datetime, timedelta
from enum import Enum

from pypika.functions import Now
from pypika.queries import Query, Table
from pypika.terms import Interval
from tortoise import Model, fields, Tortoise
from tortoise.transactions import in_transaction

from anon_talks import config
from anon_talks.utils import ExistsCriterion


class TimestampMixin:
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)


class TelegramUser(TimestampMixin, Model):

    class Status(Enum):
        IN_MENU = 'in_menu'
        WAITING_OPPONENT = 'waiting_opponent'
        IN_CONVERSATION = 'in_conversation'

    tg_id = fields.BigIntField(unique=True, pk=True)
    tg_chat_id = fields.BigIntField(unique=True)
    status = fields.CharEnumField(Status, default=Status.IN_MENU, max_length=30)

    def __str__(self):
        return f'TG user {self.pk}'


class Conversation(TimestampMixin, Model):
    id = fields.IntField(pk=True)
    initiator = fields.ForeignKeyField('anon_talks.TelegramUser', related_name='started_conversations')
    opponent = fields.ForeignKeyField('anon_talks.TelegramUser', related_name='joined_conversations', null=True)
    finished_at = fields.DatetimeField(null=True)

    def __str__(self):
        return f'Conversation {self.pk}'

    @classmethod
    async def start(cls, user: TelegramUser) -> 'Conversation':
        conversation_table = Table(cls._meta.db_table)
        c1 = Table(cls._meta.db_table, alias='C1')
        params = [cls._meta.db.executor_class.parameter(None, i) for i in range(1, 5)]

        subquery = (
            Query.from_(c1)
            .select(c1.id)
            .where((((c1.opponent_id == conversation_table.initiator_id) & (c1.initiator_id == params[1]))
                   | ((c1.initiator_id == conversation_table.opponent_id) & (c1.opponent_id == params[2])))
                   & c1.finished_at > params[3])  # is recent
        )
        query = (
            Query.from_(conversation_table)
            .select(conversation_table.id, conversation_table.finished_at)
            .limit(1)
            .where(conversation_table.opponent_id.isnull()
                   & (conversation_table.initiator_id != params[0])  # not own created
                   & ExistsCriterion(subquery).negate())  # should not have the same recent opponent
        )

        time_limit = datetime.now() - timedelta(minutes=config.RECENT_OPPONENT_TIMEOUT)
        connection = Tortoise.get_connection('anon_talks')

        __, suitable_conversations = await connection.execute_query(query.get_sql(), ([user.tg_id] * 3) + [time_limit])
        if suitable_conversations:
            conversation = await cls.all().select_related('initiator').get(id=suitable_conversations[0][0])
            conversation.opponent = user
            conversation.initiator.status = conversation.opponent.status = TelegramUser.Status.IN_CONVERSATION
            await asyncio.gather(
                conversation.save(update_fields=['opponent_id', 'modified_at']),
                conversation.initiator.save(update_fields=['status']),
                conversation.opponent.save(update_fields=['status']),
            )
        else:
            user.status = TelegramUser.Status.WAITING_OPPONENT
            conversation, __ = await asyncio.gather(
                cls.create(initiator=user),
                user.save(update_fields=['status']),
            )

        return conversation
