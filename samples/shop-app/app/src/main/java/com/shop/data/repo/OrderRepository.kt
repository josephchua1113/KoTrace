package com.shop.data.repo

import com.shop.data.remote.OrderService
import javax.inject.Inject

// Pattern D: the Repository is consumed by a UseCase, not by a ViewModel
class OrderRepository @Inject constructor(private val orderService: OrderService) {

    suspend fun fetchOrders(): List<Order> = loadRemote()

    private suspend fun loadRemote(): List<Order> = orderService.getOrders()
}
