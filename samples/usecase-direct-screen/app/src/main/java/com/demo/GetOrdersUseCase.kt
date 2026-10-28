package com.demo

// Calls the Service, but no Fragment, Activity, ViewModel or Repository calls it -> broken path
class GetOrdersUseCase(private val service: UserService) {
    suspend fun execute() = service.getOrders()
}
