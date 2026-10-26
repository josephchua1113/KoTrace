package com.shop.ui.cart

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.shop.domain.GetCartUseCase
import com.shop.domain.RemoveCartItemUseCase
import kotlinx.coroutines.launch

class CartViewModel(
    private val getCart: GetCartUseCase,
    private val removeItem: RemoveCartItemUseCase
) : ViewModel() {

    fun refresh() {
        viewModelScope.launch { getCart.execute() }
    }

    fun onRemove(id: String) {
        viewModelScope.launch { removeItem.remove(id) }
    }
}
