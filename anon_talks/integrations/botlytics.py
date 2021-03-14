import aiohttp
import ujson


class BotlyticsClient:
    API_URL = 'http://botlytics.co/api/v1/'

    KIND_INCOMING = 'incoming'
    KIND_OUTGOING = 'outgoing'

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._session = aiohttp.ClientSession(json_serialize=ujson.dumps)

    async def send_message(self, text, kind, conversation_id=None, sender_id=None):
        """
        Perform an API call to send a message to analytics service.

        https://botlytics.api-docs.io/v1/messages/
        """
        if kind not in (self.KIND_INCOMING, self.KIND_OUTGOING):
            raise ValueError(f'Invalid kind, must be "{self.KIND_INCOMING}" or "{self.KIND_OUTGOING}"')

        payload = {
            'text': text,
            'kind': kind,
            'conversation_identifier': conversation_id,
            'sender_identifier': sender_id
        }
        url = f'{self.API_URL}messages'
        params = {'token': self._api_key}
        async with self._session.post(url, params=params, json={'message': payload}) as response:
            result = await response.json(loads=ujson.loads)
            return result

    async def close_session(self):
        await self._session.close()
