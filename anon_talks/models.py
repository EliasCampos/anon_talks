import asyncio
from datetime import datetime, timedelta
from enum import Enum

from pypika import PostgreSQLQuery as Query
from pypika.queries import Table
from tortoise import Model, fields, Tortoise
from tortoise.queryset import QuerySet
from tortoise.query_utils import Q

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


class ConversationQuerySet(QuerySet):

    def in_progress(self):
        return self.filter(opponent_id__isnull=False, finished_at__isnull=True)

    def with_user_participant(self, user: 'TelegramUser'):
        return self.filter(Q(initiator=user) | Q(opponent=user))

    def waiting_opponent(self):
        return self.filter(opponent_id__isnull=True, finished_at__isnull=True)


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
        params = [cls._meta.db.executor_class.parameter(None, i) for i in range(4)]

        subquery = (
            Query.from_(c1)
            .select(c1.id)
            .where((((c1.opponent_id == conversation_table.initiator_id) & (c1.initiator_id == params[1]))
                   | ((c1.initiator_id == conversation_table.opponent_id) & (c1.opponent_id == params[2])))
                   & c1.finished_at > params[3])  # is recent
        )
        query = (
            Query.from_(conversation_table)
            .select(conversation_table.id)
            .limit(1)
            .where(conversation_table.opponent_id.isnull()
                   & conversation_table.finished_at.isnull()
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

    @classmethod
    def in_progress(cls):
        return cls._qs().in_progress()

    @classmethod
    def with_user_participant(cls, user: TelegramUser):
        return cls._qs().with_user_participant(user=user)

    @classmethod
    def waiting_opponent(cls):
        return cls._qs().waiting_opponent()

    def get_opponent(self, user: TelegramUser):
        if user.tg_id == self.opponent_id:
            return self.initiator
        return self.opponent

    async def finish(self):
        member_users = [self.initiator]
        if self.opponent_id:
            member_users.append(self.opponent)

        self.finished_at = datetime.now()
        coros = [self.save(update_fields=['finished_at'])]
        for user in member_users:
            user.status = TelegramUser.Status.IN_MENU
            coros.append(user.save(update_fields=['status']))

        await asyncio.gather(*coros)

    @classmethod
    def _qs(cls):
        return ConversationQuerySet(model=cls)
