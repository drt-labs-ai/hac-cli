// @meta
// name: Get Order Status
// description: Retrieves order details and status by order code
// category: orders
// tags: [order, search, information]
// params: [orderCode]
// @end

def orderCode = binding.hasVariable("orderCode") ? orderCode : "00000001"

import de.hybris.platform.servicelayer.search.FlexibleSearchService
import de.hybris.platform.core.Registry

def flexSearch = Registry.getApplicationContext().getBean(FlexibleSearchService.class)

def query = "SELECT {pk} FROM {Order} WHERE {code} = ?code"
def result = flexSearch.search(query, [code: orderCode])

if (result.result.isEmpty()) {
    println "Order not found: ${orderCode}"
    return
}

def order = result.result[0]
println "Code:     ${order.code}"
println "Status:   ${order.status}"
println "Customer: ${order.user?.uid}"
println "Total:    ${order.totalPrice} ${order.currency?.isocode}"
println "Date:     ${order.date}"
println "Entries:  ${order.entries?.size()}"
