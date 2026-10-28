package com.demo
interface UserService {
    @GET("users")
    suspend fun getUsers(): List<User>
    @GET("profile")
    suspend fun getProfile(): Profile
}
