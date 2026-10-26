package com.shop.domain

import com.shop.data.remote.ProductService
import javax.inject.Inject

class GetProductsUseCase @Inject constructor(
    private val productService: ProductService
) {
    suspend fun fetch(): List<Product> = productService.getProducts()

    suspend fun fetchDetail(id: String): Product = productService.getProductDetail(id)
}
