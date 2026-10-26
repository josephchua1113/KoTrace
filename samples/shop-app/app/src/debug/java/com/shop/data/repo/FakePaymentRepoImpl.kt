package com.shop.data.repo

class FakePaymentRepoImpl : PaymentRepo {
    override suspend fun submit(request: PaymentRequest): PaymentResult = PaymentResult.Success
}
