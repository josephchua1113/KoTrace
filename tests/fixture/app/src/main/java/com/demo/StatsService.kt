package com.demo
import retrofit2.http.GET
interface StatsService {
    @GET("v1/stats")
    suspend fun getStats(): Stats
}
