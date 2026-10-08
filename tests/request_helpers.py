from types import SimpleNamespace
from unittest.mock import AsyncMock

def request_input(id=7, payload=None, **query):
    if hasattr(payload, 'model_dump'):
        payload = payload.model_dump(mode='json', exclude_unset=True)
    return SimpleNamespace(path_params={'id': str(id)}, query_params=query,
                           json=AsyncMock(return_value=payload))
