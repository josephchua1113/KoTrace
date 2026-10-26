package com.demo
import javax.inject.Inject
class GetOrdersUseCase @Inject constructor(private val orderApi: OrderService) {
    suspend fun invokeIt(): List<Order> = orderApi.getOrders()
}
