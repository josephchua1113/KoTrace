package com.shop.data.repo

import com.shop.data.remote.PaymentService
import javax.inject.Inject

class PaymentRepoImpl @Inject constructor(
    private val paymentService: PaymentService
) : PaymentRepo {
    override suspend fun submit(request: PaymentRequest): PaymentResult =
        paymentService.pay(request)
}
