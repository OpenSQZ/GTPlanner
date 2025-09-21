import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import aiohttp
import asyncio
import os

from agent.utils.URL_to_Markdown import JinaWebClient

@pytest.fixture
def mock_aiohttp_session():
    """Fixture to mock aiohttp.ClientSession."""
    with patch("aiohttp.ClientSession") as mock_session:
        yield mock_session

# @pytest.mark.anyio
# async def test_url_to_markdown_success(mock_aiohttp_session):
#     """Test successful URL to Markdown conversion."""
#     mock_response = AsyncMock()
#     mock_response.raise_for_status = AsyncMock()

#     mock_json = MagicMock()
#     mock_json.__getitem__.side_effect = {"code": 200, "data": {"content": "Hello, world!"}}.__getitem__
#     mock_response.json = AsyncMock(return_value=mock_json)

#     mock_session_instance = mock_aiohttp_session.return_value.__aenter__.return_value

#     mock_get_context_manager = AsyncMock()
#     mock_get_context_manager.__aenter__.return_value = mock_response

#     mock_session_instance.get = AsyncMock(return_value=mock_get_context_manager)

#     client = JinaWebClient(api_key="test_key")
#     result = await client.url_to_markdown("https://example.com")

#     result.__getitem__.assert_called_with("code")
#     result.__getitem__.return_value.__getitem__.assert_called_with("content")

@pytest.mark.anyio
async def test_get_content_success():
    """Test successful content extraction."""
    client = JinaWebClient(api_key="test_key")
    with patch.object(client, "url_to_markdown", new_callable=AsyncMock) as mock_url_to_markdown:
        mock_url_to_markdown.return_value = {
            "code": 200,
            "data": {"content": "Test content"}
        }
        content = await client.get_content("https://example.com")
        assert content == "Test content"

@pytest.mark.anyio
async def test_get_content_failure():
    """Test content extraction failure."""
    client = JinaWebClient(api_key="test_key")
    with patch.object(client, "url_to_markdown", new_callable=AsyncMock) as mock_url_to_markdown:
        mock_url_to_markdown.return_value = {"code": 500, "status": "Error"}
        with pytest.raises(Exception, match="获取内容失败: Error"):
            await client.get_content("https://example.com")

@pytest.mark.anyio
async def test_get_page_info_success():
    """Test successful page info extraction."""
    client = JinaWebClient(api_key="test_key")
    with patch.object(client, "url_to_markdown", new_callable=AsyncMock) as mock_url_to_markdown:
        mock_url_to_markdown.return_value = {
            "code": 200,
            "data": {
                "title": "Test Title",
                "description": "Test Description",
                "url": "https://example.com",
                "content": "Test content"
            }
        }
        info = await client.get_page_info("https://example.com")
        assert info["title"] == "Test Title"
        assert info["description"] == "Test Description"
        assert info["url"] == "https://example.com"
        assert info["content"] == "Test content"

def test_get_usage_info():
    """Test usage info extraction."""
    client = JinaWebClient(api_key="test_key")
    result = {
        "data": {"usage": {"tokens": 100}},
        "meta": {"usage": {"tokens": 200}}
    }
    usage = client.get_usage_info(result)
    assert usage["tokens"] == 100

    result_meta = {
        "meta": {"usage": {"tokens": 200}}
    }
    usage_meta = client.get_usage_info(result_meta)
    assert usage_meta["tokens"] == 200

@pytest.mark.anyio
async def test_batch_convert():
    """Test batch conversion."""
    client = JinaWebClient(api_key="test_key")
    urls = ["https://example.com", "https://example.org"]

    with patch.object(client, "get_page_info", new_callable=AsyncMock) as mock_get_page_info:
        mock_get_page_info.side_effect = [
            {
                "title": "Example Domain",
                "description": "",
                "url": "https://example.com",
                "content": "Example Domain"
            },
            Exception("Test error")
        ]

        results = await client.batch_convert(urls)

        assert "https://example.com" in results
        assert results["https://example.com"]["title"] == "Example Domain"

        assert "https://example.org" in results
        assert "error" in results["https://example.org"]
        assert results["https://example.org"]["error"] == "Test error"

def test_init_with_api_key():
    """Test initialization with an API key."""
    client = JinaWebClient(api_key="my_secret_key")
    assert client.api_key == "my_secret_key"

@patch("agent.utils.URL_to_Markdown.get_jina_api_key", return_value="jina_key")
def test_init_with_jina_api_key(mock_get_key):
    """Test initialization with get_jina_api_key."""
    client = JinaWebClient()
    assert client.api_key == "jina_key"

@patch.dict(os.environ, {"JINA_API_KEY": "env_key"})
@patch("agent.utils.URL_to_Markdown.get_jina_api_key", return_value=None)
def test_init_with_env_variable(mock_get_key):
    """Test initialization with an environment variable."""
    client = JinaWebClient()
    assert client.api_key == "env_key"

@patch("agent.utils.URL_to_Markdown.get_jina_api_key", return_value=None)
def test_init_no_api_key(mock_get_key):
    """Test initialization without an API key."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="API密钥未设置"):
            JinaWebClient()

@pytest.mark.anyio
async def test_url_to_markdown_client_error(mock_aiohttp_session):
    """Test URL to Markdown with a client error."""
    mock_session_instance = mock_aiohttp_session.return_value.__aenter__.return_value
    mock_session_instance.get = AsyncMock(side_effect=aiohttp.ClientError("Client Error"))

    client = JinaWebClient(api_key="test_key")
    with pytest.raises(Exception, match="Jina Web API调用失败: Client Error"):
        await client.url_to_markdown("https://example.com")

@pytest.mark.anyio
async def test_url_to_markdown_timeout_error(mock_aiohttp_session):
    """Test URL to Markdown with a timeout error."""
    mock_session_instance = mock_aiohttp_session.return_value.__aenter__.return_value
    mock_session_instance.get = AsyncMock(side_effect=asyncio.TimeoutError("Timeout Error"))

    client = JinaWebClient(api_key="test_key")
    with pytest.raises(Exception, match="Jina Web API超时: Timeout Error"):
        await client.url_to_markdown("https://example.com")
