package com.demo

interface UserService {

    @POST("auth")
    suspend fun getAuth(@Body token: String): Response<AuthResponse>
}
