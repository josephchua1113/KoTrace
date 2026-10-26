package com.shop.ui.catalog

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.shop.data.repo.ProductRepo
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class CatalogViewModel @Inject constructor(
    private val productRepo: ProductRepo
) : ViewModel() {

    private val _items = MutableStateFlow<List<Product>>(emptyList())

    fun loadCatalog() {
        viewModelScope.launch { _items.value = productRepo.loadCatalog() }
    }

    fun openProduct(id: String) {
        viewModelScope.launch { productRepo.loadDetail(id) }
    }
}
