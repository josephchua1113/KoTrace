package com.shop.data.remote

import com.shop.data.remote.ApiConstants.BASE
import com.shop.data.remote.ApiConstants.PRODUCTS
import okhttp3.ResponseBody
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Url

interface ProductService {

    // (c) concatenation of two imported consts
    @GET(BASE + PRODUCTS)
    suspend fun getProducts(): List<Product>

    // (b) const declared in this file's companion object
    @GET(PRODUCT_DETAIL)
    suspend fun getProductDetail(@Path("id") id: String): Product

    // (d) dynamic @Url
    @GET
    suspend fun downloadImage(@Url url: String): ResponseBody

    // (e) const that is declared nowhere -> Unresolved
    @GET(PROMO_PATH)
    suspend fun getPromos(): List<Promo>

    companion object {
        const val PRODUCT_DETAIL = "api/v2/products/{id}"
    }
}
