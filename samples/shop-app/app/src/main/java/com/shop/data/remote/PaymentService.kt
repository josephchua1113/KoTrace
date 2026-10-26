package com.shop.data.remote

import retrofit2.http.Body
import retrofit2.http.POST

interface PaymentService {
    @POST("api/v2/payments")
    suspend fun pay(@Body request: PaymentRequest): PaymentResult
}
