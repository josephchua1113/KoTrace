package com.other

interface UserService {
    @POST("users/register")
    suspend fun register(@Body req: RegisterRequest): Response<Unit>
}
