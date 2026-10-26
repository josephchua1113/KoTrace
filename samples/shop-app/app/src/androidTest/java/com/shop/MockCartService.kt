package com.shop

// under /androidTest -> excluded
interface MockCartService {
    @retrofit2.http.GET("mock")
    suspend fun mock(): String
}
