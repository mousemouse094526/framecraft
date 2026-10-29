# fastapi

**Kind:** library

**Version:** 0.162.0, with pydantic 2.14.1

**Docs:** https://fastapi.tiangolo.com/ (pydantic: https://pydantic.dev/docs/validation/latest/llms.txt)

## Best practices

- Group path operations in an `APIRouter`; give `prefix` without a trailing `/` — [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- `app.include_router(router, prefix=...)` adds settings without changing the router — [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- Import router modules, not their `router` names, so two `router` variables do not shadow each other — [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- Prefer a return type annotation; use `response_model=` when the returned object is not that type — [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
- When both are set, `response_model` wins and output is filtered to its fields — [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
- Write `TestClient` tests as plain `def`, without `await`; `TestClient` needs `httpx` installed — [Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- Pydantic v2 uses `model_dump()`, `model_validate()` and `model_config` in place of v1 `dict()`, `parse_obj()` and `Config` — [Pydantic migration](https://pydantic.dev/docs/validation/latest/get-started/migration/)
- **Avoid:** mutating `router.routes`; it is an internal tree since 0.137.0 — [Release notes 0.137.0](https://fastapi.tiangolo.com/release-notes/)

## Pattern

```python
class DiskInfo(BaseModel):
    free_bytes: int
    note: str | None = None

router = APIRouter(prefix="/disk")

@router.get("")
def get_disk() -> DiskInfo:
    return read_disk()

# app.include_router(disk.router, prefix="/api")
def test_get_disk():
    assert TestClient(app).get("/api/disk").status_code == 200
```

Follows [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) and [Testing](https://fastapi.tiangolo.com/tutorial/testing/).

## Traps

- In Pydantic v2, `x: str | None` with no default is required (it only allows `None`); add `= None` to make it optional — [Pydantic migration](https://pydantic.dev/docs/validation/latest/get-started/migration/)
- Extra input fields are ignored by default, not rejected — [Pydantic models](https://pydantic.dev/docs/validation/latest/concepts/models/)
- `pydantic.v1` models are not supported since 0.128.0 — [Release notes 0.128.0](https://fastapi.tiangolo.com/release-notes/)
- JSON requests without a JSON `Content-Type` are rejected by default since 0.132.0 — [Release notes 0.132.0](https://fastapi.tiangolo.com/release-notes/)
- A return annotation that is not a valid Pydantic type (`Response | dict`) errors unless `response_model=None` — [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/)
- `TestClient` does not accept Pydantic models in `json=`; convert them with `jsonable_encoder` first — [Testing](https://fastapi.tiangolo.com/tutorial/testing/)

## Starlette 1.10.0 (comes with fastapi)

- `TrustedHostMiddleware(allowed_hosts=[...])` compares the `Host` header without its port; IPv6 hosts keep their brackets, so allow `"[::1]"`. A bad host gets `400` "Invalid host header" — [Starlette middleware](https://www.starlette.io/middleware/#trustedhostmiddleware)
- `TestClient`'s default host is `testserver`, which a trusted-host list without it rejects; pass `base_url="http://127.0.0.1"` — [Starlette middleware](https://www.starlette.io/middleware/#trustedhostmiddleware)
- A `lifespan` only runs when `TestClient` is used as a context manager (`with TestClient(app) as client:`) — [Testing › Lifespan](https://fastapi.tiangolo.com/advanced/testing-events/)

## Sources

- [Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) — `APIRouter`, `include_router`, prefix (accessed 2026-10-29)
- [Response Model](https://fastapi.tiangolo.com/tutorial/response-model/) — return type vs `response_model` (accessed 2026-10-29)
- [Testing](https://fastapi.tiangolo.com/tutorial/testing/) — `TestClient`, `httpx` (accessed 2026-10-29)
- [Release notes](https://fastapi.tiangolo.com/release-notes/) — breaking changes 0.128.0 to 0.162.0 (accessed 2026-10-29)
- [Pydantic migration guide](https://pydantic.dev/docs/validation/latest/get-started/migration/) — required and nullable fields, v2 renames (accessed 2026-10-29)
- [Pydantic models](https://pydantic.dev/docs/validation/latest/concepts/models/) — `BaseModel`, extra data (accessed 2026-10-29)
- [Starlette middleware](https://www.starlette.io/middleware/#trustedhostmiddleware) — `TrustedHostMiddleware` (accessed 2026-10-29)
- [Testing events: lifespan](https://fastapi.tiangolo.com/advanced/testing-events/) — `with TestClient(app)` (accessed 2026-10-29)
