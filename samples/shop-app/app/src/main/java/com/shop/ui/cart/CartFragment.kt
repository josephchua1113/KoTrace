package com.shop.ui.cart

import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels

class CartFragment : Fragment() {

    private val cartViewModel: CartViewModel by activityViewModels()

    override fun onResume() {
        super.onResume()
        cartViewModel.refresh()
    }

    fun onSwipeToDelete(id: String) {
        cartViewModel.onRemove(id)
    }
}
