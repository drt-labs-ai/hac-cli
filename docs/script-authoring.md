# Script Authoring Guide

## File Location & Naming

Scripts live in `scripts/<category>/<snake_case_name>.groovy`.

Categories: `cache`, `catalog`, `customer`, `orders`, `flexsearch`, `impex` (future).

Files starting with `_` are ignored by the library (use for private snippets).

## Frontmatter Format

Every script should begin with a `// @meta … // @end` block:

```groovy
// @meta
// name: Human Readable Name
// description: One-line description of what the script does
// category: cache
// tags: [cache, performance, maintenance]
// params: [paramName, optionalParam]
// @end
```

Fields:
| Field | Required | Purpose |
|---|---|---|
| `name` | Recommended | Display name in TUI/CLI |
| `description` | Recommended | Shown in search results |
| `category` | Recommended | Used by `--category` filter |
| `tags` | Optional | Comma-separated, used in fuzzy search |
| `params` | Optional | Documents expected parameters |

Without frontmatter, the script is still discoverable — name is derived from
the filename (snake_case → Title Case).

## Parameter Handling

Never read a variable that might be undefined. Always use a guard:

```groovy
def orderCode = binding.hasVariable("orderCode") ? orderCode : "00000001"
```

This allows scripts to be run standalone (using the default) or parameterised
(caller sets the binding variable before execution).

## Accessing Spring Beans

```groovy
import de.hybris.platform.core.Registry

// By type (preferred — compile-safe)
import de.hybris.platform.servicelayer.user.UserService
def userService = Registry.getApplicationContext().getBean(UserService.class)

// By name (fallback for beans without a type-safe handle)
def cacheController = Registry.getApplicationContext().getBean("cacheController")
```

## Common Imports

```groovy
// FlexibleSearch
import de.hybris.platform.servicelayer.search.FlexibleSearchService

// User/Customer
import de.hybris.platform.servicelayer.user.UserService
import de.hybris.platform.core.model.user.CustomerModel

// Catalog
import de.hybris.platform.catalog.CatalogVersionService
import de.hybris.platform.catalog.synchronization.CatalogSynchronizationService

// CronJobs
import de.hybris.platform.cronjob.enums.CronJobStatus

// ModelService (for saving models)
import de.hybris.platform.servicelayer.model.ModelService
```

## Output Convention

HAC captures `stdout` (i.e., `println` output) and returns it as the script result.
Always print a meaningful summary:

```groovy
// Good
println "Cleared ${count} sessions for customer ${customerEmail}"

// Bad — no output means CLI shows "(no output)"
// silently returns
```

For errors, either let the exception propagate (HAC will capture the stacktrace) or
print an explicit error message:

```groovy
if (order == null) {
    println "ERROR: Order ${orderCode} not found"
    return
}
```

## Null Safety

SAP Commerce models are frequently nullable. Guard every field access:

```groovy
// Unsafe
println order.user.uid

// Safe
println order?.user?.uid ?: "(no user)"
```

## FlexibleSearch Pattern

```groovy
import de.hybris.platform.servicelayer.search.FlexibleSearchService
import de.hybris.platform.core.Registry

def fss = Registry.getApplicationContext().getBean(FlexibleSearchService.class)

def query = "SELECT {pk} FROM {Product} WHERE {code} = ?code AND {catalogVersion} IN (?cvs)"
def result = fss.search(query, [
    code: productCode,
    cvs : catalogVersions,
])

result.result.each { product ->
    println "${product.code}: ${product.name}"
}
println "Total: ${result.totalCount}"
```

## Commit vs Dry Run

Scripts run with `commit=false` (the default) are wrapped in a transaction that is
rolled back after execution. Use this to safely test data-modifying scripts.

To persist changes:
```bash
hac groovy run --env dev --script my_script --commit
# Or in TUI: press Ctrl+T to toggle COMMIT mode before F5
```

## Template

Copy `scripts/_templates/script.groovy.template` as your starting point.

## Testing a New Script

```bash
# Preview without running
hac scripts show cache/my_new_script

# Dry-run (no commit)
hac groovy run --env dev --script cache/my_new_script

# Confirm output, then commit if needed
hac groovy run --env dev --script cache/my_new_script --commit
```
