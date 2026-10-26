package com.shop

// under /test -> excluded
interface FakeProfileService {
    @retrofit2.http.GET("fake")
    suspend fun fake(): String
}
