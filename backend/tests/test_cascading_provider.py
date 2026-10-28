import pytest
from typing import List, Optional
from app.services.llm_provider import (
    BaseLLMProvider,
    CascadingLLMProvider,
    LLMMessage,
    LLMResponse,
)

class FailingProvider(BaseLLMProvider):
    def __init__(self, name: str):
        super().__init__(model_name=name)
        self.provider = name
        self.calls = 0

    async def generate_text(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        self.calls += 1
        raise RuntimeError(f"{self.provider} rate limited 429")

class WorkingProvider(BaseLLMProvider):
    def __init__(self, name: str, response_text: str = '{"status": "ok"}'):
        super().__init__(model_name=name)
        self.provider = name
        self.response_text = response_text
        self.calls = 0

    async def generate_text(self, messages: List[LLMMessage], **kwargs) -> LLMResponse:
        self.calls += 1
        return LLMResponse(
            content=self.response_text,
            model=self.model_name,
            provider=self.provider
        )

@pytest.mark.asyncio
async def test_cascading_provider_failover():
    p1 = FailingProvider("groq-primary")
    p2 = WorkingProvider("openrouter-backup", '{"result": "success from backup"}')
    
    cascade = CascadingLLMProvider([p1, p2])
    messages = [LLMMessage(role="user", content="hello")]
    
    resp = await cascade.generate_text(messages)
    assert resp.content == '{"result": "success from backup"}'
    assert resp.provider == "openrouter-backup"
    assert p1.calls == 1
    assert p2.calls == 1

@pytest.mark.asyncio
async def test_cascading_provider_primary_success():
    p1 = WorkingProvider("primary", '{"status": "primary worked"}')
    p2 = WorkingProvider("backup", '{"status": "backup should not run"}')
    
    cascade = CascadingLLMProvider([p1, p2])
    resp = await cascade.generate_text([LLMMessage(role="user", content="test")])
    assert resp.content == '{"status": "primary worked"}'
    assert p1.calls == 1
    assert p2.calls == 0

@pytest.mark.asyncio
async def test_cascading_provider_all_fail():
    p1 = FailingProvider("primary")
    p2 = FailingProvider("backup")
    
    cascade = CascadingLLMProvider([p1, p2])
    with pytest.raises(RuntimeError, match="All providers in cascade failed"):
        await cascade.generate_text([LLMMessage(role="user", content="test")])

