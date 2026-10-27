package com.shop.ui.orders

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.shop.domain.GetOrdersUseCase
import kotlinx.coroutines.launch

class OrderViewModel(
    getOrdersUseCase: GetOrdersUseCase
) : ViewModel() {

    // alias of a plain constructor parameter, called via operator invoke
    private val getOrders = getOrdersUseCase

    fun refreshOrders() {
        viewModelScope.launch { getOrders() }
    }
}
