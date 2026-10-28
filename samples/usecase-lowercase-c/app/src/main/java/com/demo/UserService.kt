package com.demo

interface UserService {
    @GET("users/{id}")
    suspend fun getUser(@Path("id") id: String): Response<UserResponse>

    @POST("auth")
    suspend fun getAuth(@Body token: String): Response<AuthResponse>

    @GET("orders")
    suspend fun getOrders(): Response<List<OrderResponse>>
}
