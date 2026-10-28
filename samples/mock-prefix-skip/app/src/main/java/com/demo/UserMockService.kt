package com.demo

import retrofit2.Response
import retrofit2.http.GET

// Skipped: the file name contains "Mock" (not just as a prefix).
interface UserMockService {
    @GET("mock/users")
    suspend fun getMockUsers(): Response<UserResponse>
}
