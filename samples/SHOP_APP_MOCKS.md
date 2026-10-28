# shop-app mock samples

Location: `C:\Users\Joseph\Documents\kotrace\samples\shop-app`. 31 `.kt` files, 24 should pass the Step 0 filter.

## File tree

```
expected_files.csv
expected_matrix.csv
expected_unresolved.csv
app/
  build/
    generated/
      source/
        kapt/
          com/
            shop/
              GeneratedApiService.kt
  src/
    androidTest/
      java/
        com/
          shop/
            MockCartService.kt
    debug/
      java/
        com/
          shop/
            data/
              repo/
                FakePaymentRepoImpl.kt
    main/
      java/
        com/
          shop/
            data/
              remote/
                ApiConstants.kt
                CartService.kt
                Legacyservice.kt
                PaymentService.kt
                ProductService.kt
                ProfileService.kt
              repo/
                PaymentRepo.kt
                PaymentRepoImpl.kt
                ProductRepo.kt
                ProductRepoHelper.kt
                ProductRepoImpl.kt
                ProductRepositoryImpl.kt
                ProfileRepository.kt
            domain/
              GetCartUseCase.kt
              GetProductsUseCase.kt
              RemoveCartItemUseCase.kt
            ui/
              cart/
                CartFragment.kt
                CartViewModel.kt
                CheckoutFragment.kt
              catalog/
                CatalogFragment.kt
                CatalogViewModel.kt
              payment/
                PaymentFragment.kt
                PaymentViewModel.kt
              profile/
                ProfileFragment.kt
                ProfileViewModel.kt
              settings/
                SettingsActivity.kt
                SettingsViewModel.kt
    test/
      java/
        com/
          shop/
            FakeProfileService.kt
```

## Pattern A: Service > UseCase > Repository > ViewModel > Fragment

Expected rows: getProducts → fetch → **loadCatalog** (walked up from private `withRetry` → `fetchRemote`) → loadCatalog → onViewCreated, and getProductDetail → fetchDetail → loadDetail → openProduct → onItemClicked.

**main/java/com/shop/data/remote/ProductService.kt**

```kotlin
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
```

**main/java/com/shop/data/remote/ApiConstants.kt**

```kotlin
package com.shop.data.remote

object ApiConstants {
    const val BASE = "api/v2"
    const val PRODUCTS = "/products"
    const val CART_ITEMS = "api/v2/cart/items"
}
```

**main/java/com/shop/domain/GetProductsUseCase.kt**

```kotlin
package com.shop.domain

import com.shop.data.remote.ProductService
import javax.inject.Inject

class GetProductsUseCase @Inject constructor(
    private val productService: ProductService
) {
    suspend fun fetch(): List<Product> = productService.getProducts()

    suspend fun fetchDetail(id: String): Product = productService.getProductDetail(id)
}
```

**main/java/com/shop/data/repo/ProductRepo.kt**

```kotlin
package com.shop.data.repo

interface ProductRepo {
    suspend fun loadCatalog(): List<Product>
    suspend fun loadDetail(id: String): Product
}
```

**main/java/com/shop/data/repo/ProductRepoImpl.kt**

```kotlin
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
```

**main/java/com/shop/ui/catalog/CatalogViewModel.kt**

```kotlin
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
```

**main/java/com/shop/ui/catalog/CatalogFragment.kt**

```kotlin
package com.shop.ui.catalog

import android.os.Bundle
import android.view.View
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class CatalogFragment : Fragment(R.layout.fragment_catalog) {

    // delegation with generic type argument
    private val viewModel by viewModels<CatalogViewModel>()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewModel.loadCatalog()
    }

    private fun onItemClicked(id: String) {
        viewModel.openProduct(id)
    }
}
```

## Pattern B: Service > UseCase > ViewModel > Fragment

Expected rows: getCartItems → execute → refresh → CartFragment.onResume **and** CheckoutFragment.onStart (fan-out = 2 rows); removeItem (`@HTTP path=`) → remove (Koin `by inject()`) → onRemove → onSwipeToDelete.

**main/java/com/shop/data/remote/CartService.kt**

```kotlin
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
```

**main/java/com/shop/domain/GetCartUseCase.kt**

```kotlin
package com.shop.domain

import com.shop.data.remote.CartService

// constructor injection without @Inject (manual DI)
class GetCartUseCase(private val cartService: CartService) {
    suspend fun execute(): List<CartItem> = cartService.getCartItems()
}
```

**main/java/com/shop/domain/RemoveCartItemUseCase.kt**

```kotlin
package com.shop.domain

import com.shop.data.remote.CartService
import org.koin.core.component.KoinComponent
import org.koin.core.component.inject

// Koin property injection: by inject()
class RemoveCartItemUseCase : KoinComponent {
    private val cartService: CartService by inject()

    suspend fun remove(id: String) = cartService.removeItem(id, RemoveReason.USER)
}
```

**main/java/com/shop/ui/cart/CartViewModel.kt**

```kotlin
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
```

**main/java/com/shop/ui/cart/CartFragment.kt**

```kotlin
package com.shop.ui.cart

import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels

class CartFragment : Fragment() {

    private val cartViewModel: CartViewModel by activityViewModels()

    override fun onResume() {
        super.onResume()
        cartViewModel.refresh()
    }

    fun onSwipeToDelete(id: String) {
        cartViewModel.onRemove(id)
    }
}
```

**main/java/com/shop/ui/cart/CheckoutFragment.kt**

```kotlin
package com.shop.ui.cart

import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels

class CheckoutFragment : Fragment() {

    private val cartViewModel: CartViewModel by activityViewModels()

    override fun onStart() {
        super.onStart()
        cartViewModel.refresh()
    }
}
```

## Pattern C: Service > Repository > ViewModel > Fragment

Expected row: getProfile → ProfileRepository.getProfile (`@Inject lateinit var`) → loadProfile → onViewCreated. `updateProfile` is called from private `pushUpdate`, which walks up to the plain public `fun saveProfile` → ProfileViewModel.save → ProfileFragment (second Pattern C row). `getAvatar` is never called → **Unresolved link**.

**main/java/com/shop/data/remote/ProfileService.kt**

```kotlin
package com.shop.data.remote

import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PUT

interface ProfileService {

    @GET("api/v2/profile")
    suspend fun getProfile(): Profile

    @PUT("api/v2/profile")
    suspend fun updateProfile(@Body profile: Profile): Profile

    // never called anywhere -> Unresolved link
    @GET("api/v2/profile/avatar")
    suspend fun getAvatar(): Avatar
}
```

**main/java/com/shop/data/repo/ProfileRepository.kt**

```kotlin
package com.shop.data.repo

import com.shop.data.remote.ProfileService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import javax.inject.Inject

class ProfileRepository @Inject constructor() {

    // field injection
    @Inject lateinit var profileService: ProfileService

    suspend fun getProfile(): Profile = profileService.getProfile()

    // public but neither override nor suspend: the private call below has no valid entry
    fun saveProfile(profile: Profile) {
        CoroutineScope(Dispatchers.IO).launch { pushUpdate(profile) }
    }

    private suspend fun pushUpdate(profile: Profile) = profileService.updateProfile(profile)
}
```

**main/java/com/shop/ui/profile/ProfileViewModel.kt**

```kotlin
package com.shop.ui.profile

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.shop.data.repo.ProfileRepository
import kotlinx.coroutines.launch
import javax.inject.Inject

class ProfileViewModel @Inject constructor(
    private val profileRepository: ProfileRepository
) : ViewModel() {

    fun loadProfile() = viewModelScope.launch { profileRepository.getProfile() }

    fun save(profile: Profile) {
        profileRepository.saveProfile(profile)
    }
}
```

**main/java/com/shop/ui/profile/ProfileFragment.kt**

```kotlin
package com.shop.ui.profile

import android.os.Bundle
import android.view.View
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels

class ProfileFragment : Fragment() {

    private val profileViewModel: ProfileViewModel by viewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        profileViewModel.loadProfile()
        binding.saveButton.setOnClickListener { profileViewModel.save(currentProfile()) }
    }

    private fun currentProfile(): Profile = Profile("me")
}
```

## Activity screen

SettingsViewModel calls ProfileRepository.getProfile and is used by SettingsActivity → a Pattern C row with SettingsActivity.onCreate in the Fragment columns.

**main/java/com/shop/ui/settings/SettingsViewModel.kt**

```kotlin
package com.shop.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.shop.data.repo.ProfileRepository
import kotlinx.coroutines.launch
import javax.inject.Inject

class SettingsViewModel @Inject constructor(
    private val profileRepository: ProfileRepository
) : ViewModel() {
    fun loadSettings() {
        viewModelScope.launch { profileRepository.getProfile() }
    }
}
```

**main/java/com/shop/ui/settings/SettingsActivity.kt**

```kotlin
package com.shop.ui.settings

import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity

class SettingsActivity : AppCompatActivity() {
    private val settingsViewModel: SettingsViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        settingsViewModel.loadSettings()
    }
}
```

## Edge case: Ambiguous binding

PaymentViewModel injects the `PaymentRepo` interface, which has two implementations in scope → **Ambiguous binding**, no row for `pay`.

**main/java/com/shop/data/remote/PaymentService.kt**

```kotlin
package com.shop.data.remote

import retrofit2.http.Body
import retrofit2.http.POST

interface PaymentService {
    @POST("api/v2/payments")
    suspend fun pay(@Body request: PaymentRequest): PaymentResult
}
```

**main/java/com/shop/data/repo/PaymentRepo.kt**

```kotlin
package com.shop.data.repo

interface PaymentRepo {
    suspend fun submit(request: PaymentRequest): PaymentResult
}
```

**main/java/com/shop/data/repo/PaymentRepoImpl.kt**

```kotlin
package com.shop.data.repo

import com.shop.data.remote.PaymentService
import javax.inject.Inject

class PaymentRepoImpl @Inject constructor(
    private val paymentService: PaymentService
) : PaymentRepo {
    override suspend fun submit(request: PaymentRequest): PaymentResult =
        paymentService.pay(request)
}
```

**debug/java/com/shop/data/repo/FakePaymentRepoImpl.kt**

```kotlin
package com.shop.data.repo

class FakePaymentRepoImpl : PaymentRepo {
    override suspend fun submit(request: PaymentRequest): PaymentResult = PaymentResult.Success
}
```

**main/java/com/shop/ui/payment/PaymentViewModel.kt**

```kotlin
package com.shop.ui.payment

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.shop.data.repo.PaymentRepo
import kotlinx.coroutines.launch
import javax.inject.Inject

class PaymentViewModel @Inject constructor(
    private val paymentRepo: PaymentRepo
) : ViewModel() {
    fun pay(request: PaymentRequest) {
        viewModelScope.launch { paymentRepo.submit(request) }
    }
}
```

**main/java/com/shop/ui/payment/PaymentFragment.kt**

```kotlin
package com.shop.ui.payment

import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels

class PaymentFragment : Fragment() {
    private val paymentViewModel: PaymentViewModel by viewModels()

    fun onPayClicked() {
        paymentViewModel.pay(PaymentRequest(amount = 10))
    }
}
```

## Step 0: files that must be ignored

None of these may appear anywhere in the workbook.

**main/java/com/shop/data/repo/ProductRepoHelper.kt**

```kotlin
package com.shop.data.repo

// suffix "RepoHelper" is not accepted -> must never appear
class ProductRepoHelper(private val productService: com.shop.data.remote.ProductService) {
    suspend fun warmUp() = productService.getProducts()
}
```

**main/java/com/shop/data/repo/ProductRepositoryImpl.kt**

```kotlin
package com.shop.data.repo

// suffix "Impl" alone is not accepted (only RepoImpl) -> must never appear
class ProductRepositoryImpl
```

**main/java/com/shop/data/remote/Legacyservice.kt**

```kotlin
package com.shop.data.remote

// lowercase "service": suffix match is case-sensitive -> must never appear
interface Legacyservice {
    @retrofit2.http.GET("legacy")
    suspend fun ping(): String
}
```

**test/java/com/shop/FakeProfileService.kt**

```kotlin
package com.shop

// under /test -> excluded
interface FakeProfileService {
    @retrofit2.http.GET("fake")
    suspend fun fake(): String
}
```

**androidTest/java/com/shop/MockCartService.kt**

```kotlin
package com.shop

// under /androidTest -> excluded
interface MockCartService {
    @retrofit2.http.GET("mock")
    suspend fun mock(): String
}
```

**app/build/generated/source/kapt/com/shop/GeneratedApiService.kt**

```kotlin
package com.shop

// under /build/generated -> excluded
interface GeneratedApiService {
    @retrofit2.http.GET("generated")
    suspend fun generated(): String
}
```

## Expected matrix (expected_matrix.csv)

| Service Filename | URL | URL Const | Service Function | UseCase Filename | UseCase Function | Repository Name | Repository Function | ViewModel Name | ViewModel Function | ViewModel Function Source Name | Fragment Name | Fragment Function | Pattern |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CartService.kt | api/v2/cart/items | CART_ITEMS | getCartItems | GetCartUseCase.kt | execute | - | - | CartViewModel | refresh | GetCartUseCase | CartFragment | onResume | B |
| CartService.kt | api/v2/cart/items | CART_ITEMS | getCartItems | GetCartUseCase.kt | execute | - | - | CartViewModel | refresh | GetCartUseCase | CheckoutFragment | onStart | B |
| CartService.kt | api/v2/cart/{id} | - | removeItem | RemoveCartItemUseCase.kt | remove | - | - | CartViewModel | onRemove | RemoveCartItemUseCase | CartFragment | onSwipeToDelete | B |
| ProductService.kt | api/v2/products/{id} | PRODUCT_DETAIL | getProductDetail | GetProductsUseCase.kt | fetchDetail | ProductRepoImpl | loadDetail | CatalogViewModel | openProduct | ProductRepoImpl | CatalogFragment | onItemClicked | A |
| ProductService.kt | api/v2/products | BASE, PRODUCTS | getProducts | GetProductsUseCase.kt | fetch | ProductRepoImpl | loadCatalog | CatalogViewModel | loadCatalog | ProductRepoImpl | CatalogFragment | onViewCreated | A |
| ProfileService.kt | api/v2/profile | - | getProfile | - | - | ProfileRepository | getProfile | ProfileViewModel | loadProfile | ProfileRepository | ProfileFragment | onViewCreated | C |

## Expected Unresolved (expected_unresolved.csv)

| Type | Must mention |
|---|---|
| Unresolved const | PROMO_PATH |
| Ambiguous binding | PaymentViewModel -> PaymentRepo |
| Unresolved link | SettingsViewModel.loadSettings |
| Unresolved link | ProductService.kt.downloadImage |
| Unresolved link | ProductService.kt.getPromos |
| Unresolved link | ProfileService.kt.getAvatar |
| Unresolved link | ProfileService.kt.updateProfile |
| Unresolved link | PaymentService.kt.pay |
