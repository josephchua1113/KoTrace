package com.shop.ui.payment

import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels

class PaymentFragment : Fragment() {
    private val paymentViewModel: PaymentViewModel by viewModels()

    fun onPayClicked() {
        paymentViewModel.pay(PaymentRequest(amount = 10))
    }
}
