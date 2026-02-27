# Task 1.3: Watch-Files & Caching

## 🔙 Контекст

LLM analysis (task 1.2) коштує ~400-800 tokens на запуск.
Для більшості MR Discovery результат ідентичний — CI конфіг не змінювався.

## 🎯 Мета

Watch-files mechanism: Discovery запитує LLM **один раз**, отримує список файлів для спостереження.
Наступні запуски перевіряють чи watch-files змінились → якщо ні, використовують кеш.

```
Run 1: raw_data → LLM → result + watch_files    (~500 tokens)
Run 2: check watch_files → not changed → cache   (0 tokens)
Run 3: check watch_files → not changed → cache   (0 tokens)
Run N: watch_file changed → LLM → new result     (~500 tokens)
```

## Що робити

### 1. DiscoveryCache model

```python
class DiscoveryCache(BaseModel):
    """Cached LLM discovery result."""
    repo_key: str                        # "owner/repo" або "group/project"
    result: LLMDiscoveryResult           # cached LLM response
    watch_files_snapshot: dict[str, str] # {path: sha256_hash}
    created_at: datetime
    llm_model: str                       # "gemini-1.5-flash" — для invalidation при model change
```

### 2. Storage interface

```python
class DiscoveryCacheStorage(ABC):
    """Where to store discovery cache."""

    @abstractmethod
    async def get(self, repo_key: str) -> DiscoveryCache | None:
        """Get cached result if exists."""

    @abstractmethod
    async def put(self, cache: DiscoveryCache) -> None:
        """Store discovery result."""

    @abstractmethod
    async def invalidate(self, repo_key: str) -> None:
        """Remove cached result."""
```

### 3. In-memory implementation (Beta-0.5)

```python
class InMemoryDiscoveryCache(DiscoveryCacheStorage):
    """Simple in-memory cache. Живе поки працює процес.

    Достатньо для GitHub Action (один запуск = один MR).
    Persistent storage (Redis/file) — Beta-1.
    """

    def __init__(self) -> None:
        self._cache: dict[str, DiscoveryCache] = {}

    async def get(self, repo_key: str) -> DiscoveryCache | None:
        return self._cache.get(repo_key)

    async def put(self, cache: DiscoveryCache) -> None:
        self._cache[repo_key] = cache

    async def invalidate(self, repo_key: str) -> None:
        self._cache.pop(repo_key, None)
```

### 4. Watch-files check logic

```python
async def _should_rerun_discovery(
    self,
    repo_key: str,
    repo: RepositoryProvider,
    cache_storage: DiscoveryCacheStorage,
) -> tuple[bool, DiscoveryCache | None]:
    """Check if cached result is still valid."""
    cached = await cache_storage.get(repo_key)

    if cached is None:
        return True, None  # No cache → run

    # Check each watch-file
    for path, old_hash in cached.watch_files_snapshot.items():
        try:
            content = await repo.get_file_content(repo_key, path)
            new_hash = hashlib.sha256(content.encode()).hexdigest()
            if new_hash != old_hash:
                logger.info("Watch-file changed: %s", path)
                return True, cached  # Changed → re-run
        except FileNotFoundError:
            logger.info("Watch-file removed: %s", path)
            return True, cached  # File removed → re-run

    logger.info("All watch-files unchanged, using cache")
    return False, cached  # All same → use cache
```

### 5. Snapshot creation

```python
async def _create_watch_files_snapshot(
    self,
    repo: RepositoryProvider,
    repo_key: str,
    watch_files: list[str],
) -> dict[str, str]:
    """Hash watch-files for future comparison."""
    snapshot = {}
    for path in watch_files:
        try:
            content = await repo.get_file_content(repo_key, path)
            snapshot[path] = hashlib.sha256(content.encode()).hexdigest()
        except FileNotFoundError:
            snapshot[path] = "NOT_FOUND"  # Track that file didn't exist
    return snapshot
```

## Tests

- [ ] Cache miss → повертає `(True, None)`
- [ ] Cache hit, files unchanged → повертає `(False, cached)`
- [ ] Cache hit, one file changed → повертає `(True, cached)`
- [ ] Cache hit, file deleted → повертає `(True, cached)`
- [ ] Snapshot creation → correct hashes
- [ ] InMemoryDiscoveryCache CRUD працює

## Definition of Done

- [ ] `DiscoveryCache` model
- [ ] `DiscoveryCacheStorage` ABC + InMemory implementation
- [ ] Watch-files check logic
- [ ] Інтеграція в orchestrator flow
- [ ] Тести
- [ ] `make check` passes

## Estimate: 1-1.5h

## 🔮 Beta-1

- `FileBasedDiscoveryCache` — зберігає в `.reviewbot-cache/` (для local dev)
- `RedisDiscoveryCache` — для SaaS deployment
- TTL + forced invalidation API
