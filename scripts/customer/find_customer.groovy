// @meta
// name: Find Customer
// description: Finds a customer by email and displays account details
// category: customer
// tags: [customer, search, information]
// params: [customerEmail]
// @end

def customerEmail = binding.hasVariable("customerEmail") ? customerEmail : "user@example.com"

import de.hybris.platform.servicelayer.user.UserService
import de.hybris.platform.core.Registry

def userService = Registry.getApplicationContext().getBean(UserService.class)

try {
    def customer = userService.getUserForUID(customerEmail)
    println "UID:          ${customer.uid}"
    println "Name:         ${customer.name}"
    println "Groups:       ${customer.groups*.uid.join(', ')}"
    println "Login Disabled: ${customer.loginDisabled}"
    println "Created:      ${customer.creationtime}"
} catch (Exception e) {
    println "Customer not found: ${customerEmail}"
    println "Error: ${e.message}"
}
