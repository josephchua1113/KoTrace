package com.demo

interface UserService {

    @GET("users/{id}")
    suspend fun getUser(
        @Path("id") userId: String
    ): Response<UserResponse>
}
