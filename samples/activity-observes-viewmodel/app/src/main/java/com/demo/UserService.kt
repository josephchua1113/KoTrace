package com.demo

interface UserService {

    @GET("auth")
    fun getAuth(): Call<AuthResponse>
}
