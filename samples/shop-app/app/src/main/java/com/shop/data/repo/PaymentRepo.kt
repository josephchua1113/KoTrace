package com.shop.data.repo

interface PaymentRepo {
    suspend fun submit(request: PaymentRequest): PaymentResult
}
