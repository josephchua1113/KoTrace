package com.shop.domain

import com.shop.data.repo.OrderRepository
import javax.inject.Inject

class GetOrdersUseCase @Inject constructor(
    private val orderRepository: OrderRepository
) {
    suspend operator fun invoke(): Result<List<Order>> =
        runCatching { orderRepository.fetchOrders() }
}
