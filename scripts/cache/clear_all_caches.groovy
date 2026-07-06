// @meta
// name: Clear All Caches
// description: Clears all SAP Commerce cache regions (L1 + L2)
// category: cache
// tags: [cache, performance, maintenance]
// params: []
// @end

import de.hybris.platform.core.Registry

def cacheController = Registry.getApplicationContext().getBean("cacheController")
cacheController.clearAllCaches()

println "All cache regions cleared successfully."
