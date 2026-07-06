// @meta
// name: Sync Catalog Version
// description: Triggers a synchronization from staged to online catalog version
// category: catalog
// tags: [catalog, sync, impex]
// params: [catalogId, sourceVersion, targetVersion]
// @end

def catalogId      = binding.hasVariable("catalogId")      ? catalogId      : "productCatalog"
def sourceVersion  = binding.hasVariable("sourceVersion")  ? sourceVersion  : "Staged"
def targetVersion  = binding.hasVariable("targetVersion")  ? targetVersion  : "Online"

import de.hybris.platform.catalog.CatalogVersionService
import de.hybris.platform.catalog.synchronization.CatalogSynchronizationService
import de.hybris.platform.core.Registry

def catalogVersionService = Registry.getApplicationContext().getBean(CatalogVersionService.class)
def syncService = Registry.getApplicationContext().getBean(CatalogSynchronizationService.class)

def source = catalogVersionService.getCatalogVersion(catalogId, sourceVersion)
def target = catalogVersionService.getCatalogVersion(catalogId, targetVersion)

if (!source) { println "ERROR: Source catalog version ${catalogId}/${sourceVersion} not found."; return }
if (!target) { println "ERROR: Target catalog version ${catalogId}/${targetVersion} not found."; return }

println "Starting sync: ${catalogId} ${sourceVersion} -> ${targetVersion}"
def result = syncService.synchronize(source, target, null)
println "Sync result: ${result}"
