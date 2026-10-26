package com.shop.data.repo

interface ProductRepo {
    suspend fun loadCatalog(): List<Product>
    suspend fun loadDetail(id: String): Product
}
