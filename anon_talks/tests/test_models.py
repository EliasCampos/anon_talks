from datetime import datetime, timedelta

import pytest

from anon_talks.models import Conversation, TelegramUser


pytestmark = pytest.mark.asyncio


class TestConversation:

    @pytest.mark.freeze_time("2021-03-07 12:30")
    async def test_start_no_new_opponent(self):
        user = await TelegramUser.create(tg_id=1, tg_chat_id=1)
        other_user1 = await TelegramUser.create(tg_id=2, tg_chat_id=2, status=TelegramUser.Status.WAITING_OPPONENT)
        other_user2 = await TelegramUser.create(tg_id=3, tg_chat_id=3, status=TelegramUser.Status.IN_MENU)

        recent_conversation1 = await Conversation.create(
            finished_at=datetime(2021, 3, 7, 12, 29),  # just 1 minute ago
            initiator=other_user1, opponent=user,
        )
        recent_conversation2 = await Conversation.create(
            finished_at=datetime(2021, 3, 7, 12, 29),  # just 1 minute ago
            initiator=user, opponent=other_user2,
        )

        conversation = await Conversation.start(user=user)
        assert conversation.id != recent_conversation1.id
        assert conversation.id != recent_conversation2.id
        assert conversation.initiator == user
        assert not conversation.finished_at
        assert not conversation.opponent

        await user.refresh_from_db(fields=['status'])
        assert user.status == TelegramUser.Status.WAITING_OPPONENT

    @pytest.mark.freeze_time("2021-03-07 12:30")
    async def test_start_with_new_opponent(self):
        user = await TelegramUser.create(tg_id=1, tg_chat_id=1)
        other_user = await TelegramUser.create(tg_id=2, tg_chat_id=2, status=TelegramUser.Status.WAITING_OPPONENT)

        await Conversation.create(
            finished_at=datetime(2021, 3, 7, 12, 19),  # after some time it's possible to start with the same opponent
            initiator=user, opponent=other_user,
        )
        waiting_conversation = await Conversation.create(initiator=other_user, opponent=None)

        conversation = await Conversation.start(user=user)
        assert conversation.id == waiting_conversation.id
        assert conversation.opponent == user
        assert not conversation.finished_at

        await user.refresh_from_db(fields=['status'])
        assert user.status == TelegramUser.Status.IN_CONVERSATION

        await other_user.refresh_from_db(fields=['status'])
        assert other_user.status == TelegramUser.Status.IN_CONVERSATION

    @pytest.mark.freeze_time("2021-03-07 12:30")
    async def test_start_cant_with_own_created(self):
        user = await TelegramUser.create(tg_id=1, tg_chat_id=1)
        waiting_conversation = await Conversation.create(initiator=user, opponent=None)

        conversation = await Conversation.start(user=user)
        assert conversation.id != waiting_conversation.id
        assert not conversation.opponent
        assert not conversation.finished_at
