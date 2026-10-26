package com.shop.ui.payment

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.shop.data.repo.PaymentRepo
import kotlinx.coroutines.launch
import javax.inject.Inject

class PaymentViewModel @Inject constructor(
    private val paymentRepo: PaymentRepo
) : ViewModel() {
    fun pay(request: PaymentRequest) {
        viewModelScope.launch { paymentRepo.submit(request) }
    }
}
