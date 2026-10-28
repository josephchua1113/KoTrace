package com.demo

// "usecase" (all lowercase) is not an accepted suffix -> must never appear
class GetOrdersusecase(private val service: UserService) {
    suspend fun execute() = service.getOrders()
}
