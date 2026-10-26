package com.shop.domain

import com.shop.data.remote.CartService
import org.koin.core.component.KoinComponent
import org.koin.core.component.inject

// Koin property injection: by inject()
class RemoveCartItemUseCase : KoinComponent {
    private val cartService: CartService by inject()

    suspend fun remove(id: String) = cartService.removeItem(id, RemoveReason.USER)
}
