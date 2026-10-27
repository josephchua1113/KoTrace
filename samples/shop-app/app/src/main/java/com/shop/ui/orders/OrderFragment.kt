package com.shop.ui.orders

import android.os.Bundle
import android.view.View
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels

class OrderFragment : Fragment() {
    private val orderViewModel: OrderViewModel by viewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        orderViewModel.refreshOrders()
    }
}
