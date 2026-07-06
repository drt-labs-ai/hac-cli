// @meta
// name: Clear Cache Region
// description: Clears a specific named cache region
// category: cache
// tags: [cache, performance]
// params: [regionName]
// @end

// Set regionName before running, e.g.: def regionName = "ProductRegion"
def regionName = binding.hasVariable("regionName") ? regionName : "ProductRegion"

import de.hybris.platform.core.Registry

def cacheController = Registry.getApplicationContext().getBean("cacheController")
def regionManager = cacheController.getRegionManager()

def region = regionManager.getRegion(regionName)
if (region == null) {
    println "ERROR: Cache region '${regionName}' not found."
    println "Available regions: ${regionManager.getRegions().collect { it.name }}"
    return
}

region.clearCache()
println "Cache region '${regionName}' cleared. Stats: ${region.getCacheStats()}"
