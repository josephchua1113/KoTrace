package com.shop.data.remote

import retrofit2.http.GET

interface OrderService {
    @GET("api/v2/orders")
    suspend fun getOrders(): List<Order>
}
