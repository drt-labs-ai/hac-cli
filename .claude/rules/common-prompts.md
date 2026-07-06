# Common Claude Prompts

Ready-made prompts for frequent extension tasks. Copy-paste into a new conversation.

---

## Add FlexibleSearch command

```
Create src/hac_cli/cli/cmd_flexsearch.py:
  hac fs query --env dev --query "SELECT {pk} FROM {Product}"
  hac fs query --env dev --file my_query.fxs

HAC endpoint: POST /console/flexiblesearch/api/execute
Body (form): flexibleSearchQuery=<query>, maxCount=200, itemsPerPage=20
Response: { "query": {...}, "exception": null, "resultList": [...] }

Add execute_flexsearch() to HacHttpClient (same _ensure_authenticated + _fetch_csrf_token flow).
Add FlexSearchResult domain model with headers + rows.
Add application/execute_flexsearch.py FlexSearchService (same pattern as execute_groovy.py).
Register in cli/app.py.
```

---

## Add ImpEx import command

```
Create src/hac_cli/cli/cmd_impex.py:
  hac impex import --env dev --file data.impex
  hac impex import --env dev --inline "INSERT_UPDATE Product;code[unique=true];name"

HAC endpoint: POST /console/impex/import
Body (form): scriptContent=<impex>, validationEnum=IMPORT_STRICT,
             maxThreads=1, encoding=UTF-8, _legacyMode=false
Response: HTML — check for "Import finished" vs error div (BeautifulSoup).

Add ImpexResult domain model. Parse HTML for success/error indicators.
```

---

## Add parallel execution across environments

```
Add to ExecuteGroovyService:
  async def execute_many(self, env_names: list[str], ...) -> list[ExecutionResult]:
      tasks = [self.execute(env_name=e, ...) for e in env_names]
      return await asyncio.gather(*tasks, return_exceptions=True)

Update cmd_groovy.py run command so --env accepts multiple values:
  def run(env: list[str] = typer.Option(..., "--env", "-e"), ...)

Display results in a Rich Table with per-env status column.
```

---

## Add Claude API NLP script selection

```
In application/execute_groovy.py update find_scripts_by_nlp():
  from anthropic import Anthropic
  client = Anthropic()
  scripts = self._scripts.list_scripts()
  script_list = "\n".join(f"{s.path}: {s.description}" for s in scripts)
  msg = client.messages.create(
      model="claude-haiku-4-5-20251001",
      max_tokens=100,
      messages=[{"role": "user", "content":
          f"From this list:\n{script_list}\n\nWhich script best matches: '{query}'?\n"
          "Reply with just the path, e.g. cache/clear_all_caches"}],
  )
  path = msg.content[0].text.strip()
  return [s for s in scripts if s.path == path]

Add anthropic>=0.30 to pyproject.toml dependencies.
```

---

## Add integration test for hac groovy run

```
In tests/integration/test_hac_groovy.py:
  pytestmark = pytest.mark.skipif(
      not os.getenv("HAC_TEST_URL"), reason="HAC_TEST_URL not set"
  )

  @pytest.mark.asyncio
  async def test_execute_inline_on_live_hac(hac_env, hac_client):
      ctx = ExecutionContext(environment=hac_env, script_content='println "ping"')
      result = await hac_client.execute(ctx)
      assert result.succeeded
      assert "ping" in result.output
```
