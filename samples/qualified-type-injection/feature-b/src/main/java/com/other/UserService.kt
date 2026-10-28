package com.other

interface UserService {
    @GET("admin/users/{id}")
    suspend fun getUser(@Path("id") id: String): Response<AdminUserResponse>
}
