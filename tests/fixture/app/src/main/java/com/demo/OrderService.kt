package com.demo
import retrofit2.http.GET
interface OrderService {
    @GET("v1/orders")
    suspend fun getOrders(): List<Order>
}
