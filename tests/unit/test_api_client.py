"""
API 客户端单元测试

测试 APIClient 的重试机制、错误处理和配置项
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from frontend.utils.api_client import APIClient, APIError


class TestAPIClient:
    """APIClient 测试类"""

    def test_init_default(self) -> None:
        """测试默认初始化"""
        client = APIClient()
        assert client.base_url is not None
        assert client.timeout > 0
        assert client.max_retries > 0
        assert client.retry_delay > 0

    def test_init_custom_base_url(self) -> None:
        """测试自定义 base_url"""
        client = APIClient(base_url="http://custom:9000")
        assert client.base_url == "http://custom:9000"

    def test_get_headers_without_token(self) -> None:
        """测试无 token 时的请求头"""
        client = APIClient()
        headers = client._get_headers()
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers

    def test_api_error_message(self) -> None:
        """测试 APIError 消息"""
        error = APIError("test error", status_code=500)
        assert error.message == "test error"
        assert error.status_code == 500
        assert str(error) == "test error"

    def test_api_error_without_status_code(self) -> None:
        """测试无状态码的 APIError"""
        error = APIError("test error")
        assert error.message == "test error"
        assert error.status_code is None


class TestAPIClientRetry:
    """APIClient 重试机制测试"""

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self) -> None:
        """测试超时重试"""
        client = APIClient()
        client.max_retries = 3
        client.retry_delay = 0.01  # 加快测试

        call_count = 0

        async def mock_request(*args: object, **kwargs: object) -> None:
            nonlocal call_count
            call_count += 1
            raise httpx.TimeoutException("timeout")

        with patch("httpx.AsyncClient.request", new=mock_request):
            with pytest.raises(APIError) as exc_info:
                await client._request_with_retry("GET", "http://test/api")

            assert call_count == 3
            assert "请求超时" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_on_5xx_error(self) -> None:
        """测试 5xx 错误重试"""
        client = APIClient()
        client.max_retries = 3
        client.retry_delay = 0.01

        call_count = 0

        async def mock_request(*args: object, **kwargs: object) -> None:
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 500
            response.text = "Internal Server Error"
            raise httpx.HTTPStatusError("500", request=MagicMock(), response=response)

        with patch("httpx.AsyncClient.request", new=mock_request):
            with pytest.raises(APIError) as exc_info:
                await client._request_with_retry("GET", "http://test/api")

            assert call_count == 3
            assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_no_retry_on_4xx_error(self) -> None:
        """测试 4xx 错误不重试"""
        client = APIClient()
        client.max_retries = 3

        call_count = 0

        async def mock_request(*args: object, **kwargs: object) -> None:
            nonlocal call_count
            call_count += 1
            response = MagicMock()
            response.status_code = 400
            response.text = "Bad Request"
            raise httpx.HTTPStatusError("400", request=MagicMock(), response=response)

        with patch("httpx.AsyncClient.request", new=mock_request):
            with pytest.raises(APIError) as exc_info:
                await client._request_with_retry("GET", "http://test/api")

            # 4xx 错误不应该重试
            assert call_count == 1
            assert exc_info.value.status_code == 400
            assert "客户端错误" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_retry_on_network_error(self) -> None:
        """测试网络错误重试"""
        client = APIClient()
        client.max_retries = 3
        client.retry_delay = 0.01

        call_count = 0

        async def mock_request(*args: object, **kwargs: object) -> None:
            nonlocal call_count
            call_count += 1
            raise httpx.RequestError("connection refused")

        with patch("httpx.AsyncClient.request", new=mock_request):
            with pytest.raises(APIError) as exc_info:
                await client._request_with_retry("GET", "http://test/api")

            assert call_count == 3
            assert "网络错误" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_success_after_retry(self) -> None:
        """测试重试后成功"""
        client = APIClient()
        client.max_retries = 3
        client.retry_delay = 0.01

        call_count = 0

        async def mock_request(*args: object, **kwargs: object) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("timeout")
            # 返回成功的响应
            response = MagicMock()
            response.json = MagicMock(return_value={"status": "ok"})
            response.raise_for_status = MagicMock()
            return response

        mock_client = MagicMock()
        mock_client.request = mock_request
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await client._request_with_retry("GET", "http://test/api")

            assert result == {"status": "ok"}
            assert call_count == 2


class TestAPIClientMethods:
    """APIClient HTTP 方法测试"""

    @pytest.mark.asyncio
    async def test_get_method(self) -> None:
        """测试 GET 方法"""
        client = APIClient()

        async def mock_request_with_retry(
            method: str, url: str, **kwargs: object
        ) -> dict[str, str]:
            return {"method": method, "url": url}

        client._request_with_retry = mock_request_with_retry  # type: ignore

        result = await client.get("/api/test", params={"key": "value"})
        assert result["method"] == "GET"

    @pytest.mark.asyncio
    async def test_post_method(self) -> None:
        """测试 POST 方法"""
        client = APIClient()

        async def mock_request_with_retry(
            method: str, url: str, **kwargs: object
        ) -> dict[str, str]:
            return {"method": method, "url": url}

        client._request_with_retry = mock_request_with_retry  # type: ignore

        result = await client.post("/api/test", data={"key": "value"})
        assert result["method"] == "POST"

    @pytest.mark.asyncio
    async def test_put_method(self) -> None:
        """测试 PUT 方法"""
        client = APIClient()

        async def mock_request_with_retry(
            method: str, url: str, **kwargs: object
        ) -> dict[str, str]:
            return {"method": method, "url": url}

        client._request_with_retry = mock_request_with_retry  # type: ignore

        result = await client.put("/api/test", data={"key": "value"})
        assert result["method"] == "PUT"

    @pytest.mark.asyncio
    async def test_delete_method(self) -> None:
        """测试 DELETE 方法"""
        client = APIClient()

        async def mock_request_with_retry(
            method: str, url: str, **kwargs: object
        ) -> dict[str, str]:
            return {"method": method, "url": url}

        client._request_with_retry = mock_request_with_retry  # type: ignore

        result = await client.delete("/api/test")
        assert result["method"] == "DELETE"
