package com.shop.data.repo

// suffix "RepoHelper" is not accepted -> must never appear
class ProductRepoHelper(private val productService: com.shop.data.remote.ProductService) {
    suspend fun warmUp() = productService.getProducts()
}
