package com.demo
import androidx.lifecycle.ViewModel
import javax.inject.Inject
class OrderViewModel @Inject constructor(private val getOrders: GetOrdersUseCase) : ViewModel() {
    fun loadOrders() {
        viewModelScope.launch { getOrders.invokeIt() }
    }
}
