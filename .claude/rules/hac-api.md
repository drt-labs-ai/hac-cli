# HAC API Reference

## Auth + Execute Flow

| Step | Method | URL | Notes |
|---|---|---|---|
| Login page | GET | `/login` | Extract `<input name="_csrf">` |
| Authenticate | POST | `/j_spring_security_check` | Body: `j_username`, `j_password`, `_csrf`; `follow_redirects=False` |
| CSRF for scripts | GET | `/console/scripting/` | Extract `<meta name="_csrf" content="...">` |
| Execute Groovy | POST | `/console/scripting/execute` | Form: `script`, `commit`, `scriptType=groovy`; Header: `X-CSRF-TOKEN` |
| FlexibleSearch | POST | `/console/flexiblesearch/api/execute` | Same auth pattern |
| ImpEx import | POST | `/console/impex/import` | Multipart or form body |

**Login success** = 302 → `/` or app root.
**Login failure** = 302 → `/login?error=true`.
**Session expired** = CSRF-page GET redirects to `/login`.

## Groovy Execution Response

```json
{
  "executionResult": "output or stacktrace",
  "stacktraceOccurred": false,
  "outputText": "stdout (newer SAP Commerce versions)"
}
```

Custom SAP Commerce instances may use `stacktraceText` (non-empty string = error) instead of `stacktraceOccurred` (bool). `_parse_execution_response()` in `hac_client.py` handles both.

## Dynamic Execute URL

The actual POST URL is embedded in the scripting page HTML on `id="executeButton"` as `data-executorurl`. Custom instances override this path. `_extract_execute_url_from_html()` in `hac_client.py` reads it; falls back to `env.execute_url` if absent.

## URL Construction

`Environment.hac_base_url` strips trailing slash via `url.rstrip("/")`. All URL properties (`login_url`, `scripting_url`, `execute_url`) build on `hac_base_url`. The trailing slash in config is optional — no double-slash risk.

## Required POST body fields for Groovy execute

```
script=<groovy code>
commit=true|false
scriptType=groovy        ← required; 400 without it
```
