package com.shop

// under /build/generated -> excluded
interface GeneratedApiService {
    @retrofit2.http.GET("generated")
    suspend fun generated(): String
}
