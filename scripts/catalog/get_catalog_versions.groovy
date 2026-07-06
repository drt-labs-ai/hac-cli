// @meta
// name: Get Catalog Versions
// description: Lists all catalog versions with sync status and item counts
// category: catalog
// tags: [catalog, information]
// params: []
// @end

import de.hybris.platform.catalog.CatalogService
import de.hybris.platform.core.Registry

def catalogService = Registry.getApplicationContext().getBean(CatalogService.class)

catalogService.getAllCatalogs().each { catalog ->
    println "Catalog: ${catalog.id}"
    catalog.catalogVersions.each { version ->
        println "  Version: ${version.version} | Active: ${version.active} | Items: ${version.allItems?.size() ?: 'N/A'}"
    }
}
