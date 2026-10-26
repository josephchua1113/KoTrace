package com.shop.domain

import com.shop.data.remote.CartService

// constructor injection without @Inject (manual DI)
class GetCartUseCase(private val cartService: CartService) {
    suspend fun execute(): List<CartItem> = cartService.getCartItems()
}
