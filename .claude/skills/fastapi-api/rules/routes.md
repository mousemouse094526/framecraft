# Routes

**Owns:** HTTP shape — path, method, request parsing, response model.

**Must not:** hold logic beyond calling one module function; touch the
filesystem or libraries directly.

## Shape

```python
router = APIRouter(prefix="/setup")

@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    return run_checks()
```

## Rules

- One router file per feature in `backend/routes/`, mounted in `app.py` under `/api`.
- Response models are Pydantic models; field names in snake_case.
- Errors a user should see go inside the response body, not as 5xx, when the
  spec says so (setup-status: always 200).

## Good examples

- None yet — the first ticket that touches this layer sets it.
