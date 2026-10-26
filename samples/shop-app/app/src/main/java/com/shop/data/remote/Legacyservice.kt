package com.shop.data.remote

// lowercase "service": suffix match is case-sensitive -> must never appear
interface Legacyservice {
    @retrofit2.http.GET("legacy")
    suspend fun ping(): String
}
