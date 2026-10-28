package com.example

interface UserService {
    @GET("users/{id}")
    suspend fun getUser(@Path("id") id: String): Response<UserResponse>
}
