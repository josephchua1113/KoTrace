package com.shop.data.repo

import com.shop.domain.GetProductsUseCase
import javax.inject.Inject

class ProductRepoImpl @Inject constructor(
    private val getProducts: GetProductsUseCase
) : ProductRepo {

    // public entry: must be reported instead of the private helpers below
    override suspend fun loadCatalog(): List<Product> {
        val raw = fetchRemote()
        return raw.sortedBy { it.name }
    }

    override suspend fun loadDetail(id: String): Product = getProducts.fetchDetail(id)

    // two private hops: withRetry -> fetchRemote -> loadCatalog (override)
    private suspend fun fetchRemote(): List<Product> = withRetry()

    private suspend fun withRetry(): List<Product> {
        return getProducts.fetch()
    }
}
