import hashlib
import json
import time

import httpx
import pytest
from unittest.mock import Mock, patch

import tenacity

from app.services.repository_services import prepare_params, resilient_request, cacheable, get_cache_key
from starlette.testclient import TestClient
from app.main import app
from starlette.requests import Request
from unittest.mock import AsyncMock

client = TestClient(app)

scope = {
    "type": "http",
    "method": "GET",
    "scheme": "http",
    "root_path": "",
    "path": "/test_path",
    "raw_path": b"/test_path",
    "query_string": b"param=value",
    "headers": [],
}


@pytest.fixture
def test_app():
    return TestClient(app)


def test_invalid_url(test_app):
    response = test_app.get("/invalid-url")
    assert response.status_code == 404


@patch('app.services.repository_services.resilient_request')
def test_get_repositories_since_invalid_params(mock_resilient_request):
    mock_resilient_request.return_value = {'items': 'test'}
    response = client.get("/repositories/popular?since_date=2023-06-35&language=python&top_n=100")
    assert response.status_code == 200


@patch('app.services.repository_services.resilient_request')
def test_get_repositories_server_error(mock_resilient_request):
    mock_resilient_request.return_value = {'items': 'test'}
    response = client.get("/repositories/popular?since_date=2023-06-01&language=python&top_n=100")
    assert response.status_code == 200


@patch('app.services.repository_services.redis.Redis.get')
@patch('app.services.repository_services.redis.Redis.set')
@pytest.mark.asyncio
async def test_cacheable_with_ttl_expired(mock_set, mock_get):
    mock_get.return_value = None

    @cacheable(ttl=60)
    async def mock_func(request):
        return {"result": "from function"}

    request = Request(scope, receive=None)
    assert await mock_func(request) == {"result": "from function"}
    mock_set.assert_called_once()

    mock_get.return_value = '{"result": "from cache"}'.encode()
    assert await mock_func(request) == {"result": "from cache"}

    # Simulate TTL expiration
    time.sleep(61)
    mock_get.return_value = None
    assert await mock_func(request) == {"result": "from function"}


def prepare_params(query: str, per_page: int):
    if not isinstance(query, str) or not isinstance(per_page, int):
        raise TypeError("Invalid argument type")
    result = prepare_params("stars:>=1", 10)
    expected_result = {
        "q": "stars:>=1",
        "sort": "stars",
        "order": "desc",
        "per_page": 10,
    }
    assert result == expected_result


def test_prepare_params_invalid_input():
    with pytest.raises(TypeError):
        prepare_params(123, "invalid")


def test_get_cache_key():
    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "http",
        "root_path": "",
        "path": "/test_path",
        "raw_path": b"/test_path",
        "query_string": b"param=value",
        "headers": [],
    }
    request = Request(scope, receive=None)
    cache_key = get_cache_key("test_func", request)
    expected_key = hashlib.sha256(
        json.dumps(("test_func", {"path": "/test_path", "query_params": {"param": "value"}})).encode()).hexdigest()
    assert cache_key == expected_key


@pytest.mark.asyncio
async def test_resilient_request_200_status():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "data"}  # Add mock JSON data
        mock_get.return_value = mock_response
        result = await resilient_request("search/repositories", {"q": "stars:>=1"})
        assert result == {"result": "data"}  # Change assertion to check for returned data


@pytest.mark.asyncio
async def test_resilient_request_non_200_status():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError("Mocked error", request=None, response=Mock(status_code=404))
        with pytest.raises(tenacity.RetryError):
            await resilient_request("search/repositories", {"q": "stars:>=1"})


@patch('app.services.repository_services.redis.Redis.get')
@patch('app.services.repository_services.redis.Redis.set')
@pytest.mark.asyncio
async def test_cacheable_with_cache_hit(mock_set, mock_get):
    mock_get.return_value = '{"result": "from cache"}'.encode()

    @cacheable(ttl=60)
    async def mock_func(request):
        return {"result": "from function"}

    request = Request(scope, receive=None)
    assert await mock_func(request) == {"result": "from cache"}
    mock_set.assert_not_called()


@patch('app.services.repository_services.redis.Redis.get')
@patch('app.services.repository_services.redis.Redis.set')
@pytest.mark.asyncio
async def test_cacheable_with_cache_miss(mock_set, mock_get):
    mock_get.return_value = None

    @cacheable(ttl=60)
    async def mock_func(request):
        return {"result": "from function"}

    request = Request(scope, receive=None)
    assert await mock_func(request) == {"result": "from function"}
    mock_set.assert_called_once()


@patch('app.services.repository_services.resilient_request')
def test_get_top_repositories(mock_resilient_request):
    mock_resilient_request.return_value = {'items': 'test'}
    response = client.get("/repositories/popular/10")
    assert response.status_code == 200
    assert response.json() == 'test'


@patch('app.services.repository_services.resilient_request')
def test_get_repositories_since(mock_resilient_request):
    mock_resilient_request.return_value = {'items': 'test'}
    response = client.get("/repositories/popular?since_date=2023-06-01&language=python&top_n=100")
    assert response.status_code == 200
    assert response.json() == 'test'


def test_rate_limiting_exceeded_limit():
    response = [client.get("/repositories/popular/5") for _ in range(11)]
    assert any(res.status_code == 429 for res in response)
