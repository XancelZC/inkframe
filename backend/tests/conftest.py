"""测试配置：强制使用 mock 供应商."""

import pytest
import app.api.models as models_module


@pytest.fixture(autouse=True)
def _force_mock_provider():
    """确保测试始终使用 mock 供应商."""
    models_module._active_provider_id = "mock"
    yield
