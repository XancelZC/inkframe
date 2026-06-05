"""LLM models API route — 多供应商动态管理."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.llm.registry import get_provider

router = APIRouter(tags=["models"])

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "llm_config.json"

# ── 内置 mock 供应商 ──────────────────────────────────────────────
_MOCK_PROVIDER = {
    "id": "mock",
    "name": "Mock（本地测试）",
    "type": "mock",
    "base_url": "",
    "api_key": "",
    "model": "",
    "models": [],
}

# ── 运行时状态 ────────────────────────────────────────────────────
_active_provider_id: str = "mock"
_providers: list[dict] = []


# ── 持久化 ────────────────────────────────────────────────────────
def _load_config() -> None:
    global _providers, _active_provider_id
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            _active_provider_id = data.get("active_provider_id", "mock")
            _providers = data.get("providers", [])
            # 确保 mock 存在
            if not any(p["id"] == "mock" for p in _providers):
                _providers.insert(0, dict(_MOCK_PROVIDER))
            return
        except Exception:
            pass
    _providers = [dict(_MOCK_PROVIDER)]
    _active_provider_id = "mock"


def _save_config() -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps({"active_provider_id": _active_provider_id, "providers": _providers}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _sync_env_vars() -> None:
    """根据当前 active provider 同步环境变量."""
    active = _get_provider_by_id(_active_provider_id)
    if not active:
        return
    if active["type"] == "openai_compatible":
        os.environ["OPENAI_API_KEY"] = active.get("api_key", "")
        os.environ["OPENAI_BASE_URL"] = active.get("base_url", "")
    elif active["type"] == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = active.get("api_key", "")
        os.environ["ANTHROPIC_BASE_URL"] = active.get("base_url", "")


def _get_provider_by_id(pid: str) -> Optional[dict]:
    return next((p for p in _providers if p["id"] == pid), None)


# 启动时加载
_load_config()
_sync_env_vars()


# ── 请求模型 ──────────────────────────────────────────────────────
class CreateProviderRequest(BaseModel):
    name: str
    type: str  # "openai_compatible" | "anthropic"
    base_url: str
    api_key: str
    model: str = ""


class UpdateProviderRequest(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    models: Optional[list[str]] = None


# ── API 端点 ──────────────────────────────────────────────────────
@router.get("/models/config")
def get_config():
    """返回完整配置."""
    # 返回时遮罩 api_key
    masked = []
    for p in _providers:
        cp = dict(p)
        cp["api_key_masked"] = _mask_key(cp.get("api_key", ""))
        cp["has_api_key"] = bool(cp.get("api_key"))
        masked.append(cp)
    return {"active_provider_id": _active_provider_id, "providers": masked}


@router.post("/models")
def create_provider(req: CreateProviderRequest):
    """新增供应商."""
    if req.type not in ("openai_compatible", "anthropic"):
        return {"error": "type 必须是 openai_compatible 或 anthropic"}

    pid = f"p_{uuid.uuid4().hex[:8]}"
    provider = {
        "id": pid,
        "name": req.name,
        "type": req.type,
        "base_url": req.base_url,
        "api_key": req.api_key,
        "model": req.model,
        "models": [],
    }
    _providers.append(provider)
    _save_config()
    return {"status": "created", "id": pid}


@router.put("/models/{pid}")
def update_provider(pid: str, req: UpdateProviderRequest):
    """更新供应商配置."""
    provider = _get_provider_by_id(pid)
    if not provider:
        return {"error": "供应商不存在"}
    if pid == "mock":
        return {"error": "不能修改 Mock 供应商"}

    if req.name is not None:
        provider["name"] = req.name
    if req.base_url is not None:
        provider["base_url"] = req.base_url
    if req.api_key is not None:
        provider["api_key"] = req.api_key
    if req.model is not None:
        provider["model"] = req.model
    if req.models is not None:
        provider["models"] = req.models

    _save_config()
    _sync_env_vars()
    return {"status": "saved"}


@router.delete("/models/{pid}")
def delete_provider(pid: str):
    """删除供应商."""
    global _active_provider_id
    if pid == "mock":
        return {"error": "不能删除 Mock 供应商"}
    provider = _get_provider_by_id(pid)
    if not provider:
        return {"error": "供应商不存在"}

    _providers[:] = [p for p in _providers if p["id"] != pid]
    if _active_provider_id == pid:
        _active_provider_id = "mock"
    _save_config()
    return {"status": "deleted"}


@router.put("/models/{pid}/active")
def set_active_provider(pid: str):
    """设为默认供应商."""
    global _active_provider_id
    if not _get_provider_by_id(pid):
        return {"error": "供应商不存在"}
    _active_provider_id = pid
    _save_config()
    _sync_env_vars()
    return {"status": "ok", "active_provider_id": pid}


@router.post("/models/{pid}/fetch")
def fetch_models(pid: str):
    """从供应商 API 获取可用模型列表."""
    provider = _get_provider_by_id(pid)
    if not provider:
        return {"success": False, "error": "供应商不存在"}

    api_key = provider.get("api_key", "")
    base_url = provider.get("base_url", "")

    if not api_key:
        return {"success": False, "error": "请先填写 API Key"}

    if provider["type"] == "openai_compatible":
        try:
            import httpx
            resp = httpx.get(
                f"{base_url.rstrip('/')}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=15,
            )
            if resp.status_code != 200:
                return {"success": False, "error": f"API 返回 {resp.status_code}: {resp.text[:200]}"}
            data = resp.json()
            models = sorted([m["id"] for m in data.get("data", [])])
            # 保存到供应商配置
            provider["models"] = models
            _save_config()
            return {"success": True, "models": models}
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif provider["type"] == "anthropic":
        models = [
            "claude-sonnet-4-20250514",
            "claude-haiku-4-5-20251001",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ]
        provider["models"] = models
        _save_config()
        return {"success": True, "models": models, "note": "Anthropic 无公开接口，返回已知模型"}

    return {"success": False, "error": f"不支持的协议类型: {provider['type']}"}


@router.post("/models/{pid}/test")
def test_connection(pid: str):
    """测试供应商连接."""
    provider = _get_provider_by_id(pid)
    if not provider:
        return {"success": False, "error": "供应商不存在"}

    # mock 直接通过
    if provider["type"] == "mock":
        return {"success": True, "elapsed_seconds": 0, "response": {"status": "ok"}}

    api_key = provider.get("api_key", "")
    base_url = provider.get("base_url", "")

    if not api_key:
        return {"success": False, "error": "请先填写 API Key"}

    # 设置环境变量给 provider 使用
    if provider["type"] == "openai_compatible":
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = base_url
        provider_id_for_llm = "openai_compatible"
    elif provider["type"] == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = api_key
        os.environ["ANTHROPIC_BASE_URL"] = base_url
        provider_id_for_llm = "anthropic"
    else:
        return {"success": False, "error": f"不支持的协议类型: {provider['type']}"}

    llm_provider = get_provider(provider_id_for_llm)
    if not llm_provider:
        return {"success": False, "error": f"LLM provider 未注册: {provider_id_for_llm}"}

    try:
        start = time.time()
        result = llm_provider.generate_json(
            "Return a JSON object with a single field 'status' set to 'ok'.",
            {"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]},
        )
        elapsed = round(time.time() - start, 2)
        return {"success": True, "elapsed_seconds": elapsed, "response": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── 辅助函数 ──────────────────────────────────────────────────────
def _mask_key(key: str) -> str:
    """API Key 遮罩：前5后6，中间 *****."""
    if not key:
        return ""
    if len(key) < 12:
        return "*****"
    return f"{key[:5]}*****{key[-6:]}"


def get_active_provider_id() -> str:
    return _active_provider_id


def get_active_model() -> str:
    provider = _get_provider_by_id(_active_provider_id)
    return provider.get("model", "") if provider else ""


def get_provider_type(pid: str) -> str:
    """返回供应商的协议类型."""
    provider = _get_provider_by_id(pid)
    return provider.get("type", "mock") if provider else "mock"
