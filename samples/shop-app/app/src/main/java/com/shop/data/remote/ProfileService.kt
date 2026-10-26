package com.shop.data.remote

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PUT

interface ProfileService {

    @GET("api/v2/profile")
    suspend fun getProfile(): Profile

    @PUT("api/v2/profile")
    suspend fun updateProfile(@Body profile: Profile): Profile

    // never called anywhere -> Unresolved link
    @GET("api/v2/profile/avatar")
    suspend fun getAvatar(): Avatar
}
