# Task: Multi-LLM Router Implementation

**Created:** 2026-01-19  
**Assignee:** AI Agent + Human  
**Estimated:** 4-6 hours  
**Status:** Not Started  
**Priority:** P0 (Critical for MVP)

---

## 🎯 Goal

Implement a unified LLM router that supports 4 providers (Claude, GPT, Gemini, DeepSeek) with intelligent task routing based on complexity and cost.

---

## 📋 Acceptance Criteria

- [ ] `LLMRouter` class supports all 4 providers
- [ ] Each provider has dedicated client class
- [ ] Router selects appropriate model based on `TaskComplexity`
- [ ] Fallback mechanism when provider unavailable
- [ ] Configuration via environment variables and config file
- [ ] Unit tests for each provider client
- [ ] Integration tests with real API calls (optional, can use mocks)
- [ ] Cost tracking for each API call
- [ ] Error handling with graceful degradation
- [ ] Documentation for adding new providers

---

## 🔧 Technical Approach

### Architecture

```
LLMRouter
    │
    ├── AnthropicClient (Claude Opus/Sonnet/Haiku)
    ├── OpenAIClient (GPT-4/GPT-4o/GPT-3.5)
    ├── GoogleClient (Gemini Pro/Flash)
    └── DeepSeekClient (DeepSeek-V2/Chat)
```

### Task Complexity Levels

```python
class TaskComplexity(Enum):
    TRIVIAL = 1   # No LLM (regex, AST)
    SIMPLE = 2    # Classification, extraction
    MEDIUM = 3    # Code analysis
    COMPLEX = 4   # Reasoning, synthesis
```

### Routing Logic

| Complexity | Free Tier (Solo) | Small Team | Enterprise |
|------------|------------------|------------|------------|
| TRIVIAL | None | None | None |
| SIMPLE | Gemini Flash | Haiku | Local Llama |
| MEDIUM | Haiku | Haiku/Sonnet | Local Llama |
| COMPLEX | Sonnet | Sonnet/Opus | Sonnet |

### Configuration Structure

```yaml
# .ai-reviewer.yml
llm:
  # Provider priority
  providers:
    - anthropic  # Try first
    - openai     # Fallback
    - google
    - deepseek
  
  # Provider configs
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    models:
      simple: claude-3-5-haiku-20241022
      medium: claude-3-5-sonnet-20241022
      complex: claude-opus-4-20250514
    max_tokens: 4096
    timeout: 60
  
  openai:
    api_key: ${OPENAI_API_KEY}
    models:
      simple: gpt-3.5-turbo
      medium: gpt-4o-mini
      complex: gpt-4o
  
  google:
    api_key: ${GOOGLE_API_KEY}
    models:
      simple: gemini-1.5-flash
      medium: gemini-1.5-pro
      complex: gemini-1.5-pro
  
  deepseek:
    api_key: ${DEEPSEEK_API_KEY}
    models:
      simple: deepseek-chat
      medium: deepseek-chat
      complex: deepseek-chat
  
  # Cost tracking
  track_costs: true
  cost_budget_per_review: 0.50  # USD
```

---

## 📦 Implementation Steps

### Step 1: Base Abstractions
```python
# src/ai_reviewer/llm/base.py

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel

class LLMRequest(BaseModel):
    """Standard request format."""
    prompt: str
    system: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.0

class LLMResponse(BaseModel):
    """Standard response format."""
    content: str
    model: str
    tokens_used: int
    cost_usd: float
    provider: str

class BaseLLMClient(ABC):
    """Abstract LLM client."""
    
    @abstractmethod
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Send chat request."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and reachable."""
        pass
```

### Step 2: Provider Clients

Create 4 client implementations:
- `AnthropicClient` using `anthropic` SDK
- `OpenAIClient` using `openai` SDK
- `GoogleClient` using `google-generativeai` SDK
- `DeepSeekClient` using OpenAI-compatible API

### Step 3: Router Logic

```python
# src/ai_reviewer/llm/router.py

class LLMRouter:
    """Intelligent LLM routing."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.clients = self._init_clients()
        self.cost_tracker = CostTracker()
    
    async def route(self, task: Task) -> LLMResponse:
        """Route task to appropriate LLM."""
        
        # Assess complexity
        complexity = self._assess_complexity(task)
        
        # Try providers in priority order
        for provider in self.config.providers:
            try:
                client = self.clients[provider]
                if not client.is_available():
                    continue
                
                model = self._select_model(provider, complexity)
                response = await client.chat(
                    LLMRequest(
                        prompt=task.prompt,
                        system=task.system,
                        max_tokens=task.max_tokens
                    )
                )
                
                # Track cost
                self.cost_tracker.record(response)
                
                return response
                
            except Exception as e:
                logger.warning(f"{provider} failed: {e}, trying next")
                continue
        
        raise NoProvidersAvailableError("All LLM providers failed")
```

### Step 4: Cost Tracking

```python
class CostTracker:
    """Track LLM costs."""
    
    # Prices per 1M tokens (as of 2026-01)
    COSTS = {
        "claude-opus-4": {"input": 15.0, "output": 75.0},
        "claude-sonnet-3.5": {"input": 3.0, "output": 15.0},
        "claude-haiku-3.5": {"input": 0.8, "output": 4.0},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gemini-pro": {"input": 1.25, "output": 5.0},
        "gemini-flash": {"input": 0.075, "output": 0.3},
        "deepseek-chat": {"input": 0.14, "output": 0.28},
    }
    
    def calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost for API call."""
        # Simplified: assume 50/50 input/output split
        prices = self.COSTS.get(model, {"input": 1.0, "output": 1.0})
        avg_price = (prices["input"] + prices["output"]) / 2
        return (tokens / 1_000_000) * avg_price
```

---

## 🧪 Testing Strategy

### Unit Tests
```python
# tests/unit/test_llm_router.py

def test_router_selects_cheap_model_for_simple_task():
    """Router should use cheapest model for simple tasks."""
    config = LLMConfig(providers=["anthropic"])
    router = LLMRouter(config)
    
    task = Task(complexity=TaskComplexity.SIMPLE, ...)
    model = router._select_model("anthropic", task.complexity)
    
    assert model == "claude-3-5-haiku-20241022"

def test_router_falls_back_when_provider_unavailable():
    """Router should try next provider on failure."""
    # Mock first provider to fail
    # Verify second provider is used
    pass
```

### Integration Tests (Optional)
```python
# tests/integration/test_providers.py

@pytest.mark.integration
async def test_anthropic_client_real_api():
    """Test real Anthropic API call."""
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("No API key")
    
    client = AnthropicClient(...)
    response = await client.chat(
        LLMRequest(prompt="Say 'test'", max_tokens=10)
    )
    
    assert response.content
    assert response.cost_usd > 0
```

---

## 📦 Dependencies

**Requires:**
- Pydantic models defined
- Configuration system working

**Blocks:**
- Security Agent implementation
- All other LLM-dependent features

---

## 📝 Notes

### Provider-Specific Details

**Anthropic (Claude):**
- SDK: `anthropic>=0.8`
- Best for: complex reasoning
- Free tier: None (paid only)
- Rate limits: 10 RPM (free tier equivalent)

**OpenAI (GPT):**
- SDK: `openai>=1.0`
- Best for: general purpose
- Free tier: $5 credit
- Rate limits: 3 RPM (tier 1)

**Google (Gemini):**
- SDK: `google-generativeai>=0.3`
- Best for: cost-effective simple tasks
- Free tier: 60 RPM, 1M tokens/month
- Rate limits: Generous free tier

**DeepSeek:**
- SDK: OpenAI-compatible
- Best for: code-specific tasks
- Free tier: Limited
- Rate limits: TBD

### Environment Variables Required

```bash
# Required for at least 1 provider
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=...

# Optional
LLM_PROVIDER_PRIORITY=anthropic,google,openai,deepseek
LLM_COST_BUDGET_PER_REVIEW=0.50
```

### Future Enhancements (Not in MVP)

- [ ] Local LLM support (Ollama)
- [ ] Caching of responses
- [ ] Streaming responses
- [ ] Batch processing
- [ ] A/B testing between providers

---

## 🔗 Related

- Parent: [Project Process](../GENERAL_PROJECT_DESCRIPTION/PROCESS_PROJECT.md)
- Architecture: [docs/architecture.md](../docs/architecture.md)
- Config spec: [docs/configuration.md](../docs/configuration.md)
