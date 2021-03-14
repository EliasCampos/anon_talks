import pytest

from anon_talks.integrations.botlytics import BotlyticsClient


pytestmark = pytest.mark.asyncio


@pytest.fixture
def botlytics():
    return BotlyticsClient(api_key='test_key')


@pytest.fixture
def botlytics_send_url():
    return f'{BotlyticsClient.API_URL}messages?token=test_key'


class TestBotlyticsClient:

    async def test_send_message(self, aiohttp_client_mock, botlytics, botlytics_send_url):
        payload = {
            "text": "test",
            "kind": "incoming",
            "created_at": "2021-03-14T12:24:24.802Z"
        }
        aiohttp_client_mock.post(botlytics_send_url, payload=payload)

        result = await botlytics.send_message(text='test', kind=BotlyticsClient.KIND_INCOMING, sender_id='user_007')
        assert result == payload

        request_calls = list(aiohttp_client_mock.requests.values()).pop()
        assert request_calls[0].kwargs['json'] == {
            'message': {
                'text': 'test',
                'kind': BotlyticsClient.KIND_INCOMING,
                'conversation_identifier': None,
                'sender_identifier': 'user_007'
            }
        }

    async def test_send_message_invalid_kind(self, botlytics):
        with pytest.raises(ValueError, match='.*kind.*'):
            await botlytics.send_message(text='test', kind='BAD KIND', sender_id='user_007')
