package com.shop.ui.cart

import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels

class CheckoutFragment : Fragment() {

    private val cartViewModel: CartViewModel by activityViewModels()

    override fun onStart() {
        super.onStart()
        cartViewModel.refresh()
    }
}
