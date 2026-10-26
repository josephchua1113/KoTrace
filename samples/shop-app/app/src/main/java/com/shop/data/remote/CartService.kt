package com.shop.data.remote

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.HTTP
import retrofit2.http.Path

interface CartService {

    // (b) qualified const Object.NAME
    @GET(ApiConstants.CART_ITEMS)
    suspend fun getCartItems(): List<CartItem>

    // @HTTP with path = literal
    @HTTP(method = "DELETE", path = "api/v2/cart/{id}", hasBody = true)
    suspend fun removeItem(@Path("id") id: String, @Body reason: RemoveReason)
}
