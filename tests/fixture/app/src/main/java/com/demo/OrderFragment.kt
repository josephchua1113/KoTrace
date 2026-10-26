package com.demo
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
class OrderFragment : Fragment() {
    private val orderVm: OrderViewModel by activityViewModels()
    fun onStartLoading() {
        orderVm.loadOrders()
    }
}
