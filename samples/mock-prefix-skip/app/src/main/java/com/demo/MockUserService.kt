package com.demo

interface MockUserService {
    @GET("mock/users/{id}")
    suspend fun getUser(@Path("id") userId: String): Response<UserResponse>
}
