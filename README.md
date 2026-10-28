# kt-traceability

Deterministic Service → Fragment traceability matrix for Kotlin/Android codebases.
Every link is backed by file path, line and symbol; anything unprovable is "-" and logged in the Unresolved sheet.

```
pip install openpyxl
python3 kt_traceability.py --root /path/to/android/project --out traceability_matrix.xlsx
```

Sheets: Traceability Matrix, Broken Paths, Evidence, Unresolved, plus Filtered Files and Service Endpoints for review.

**Request Object / Response Object** (after URL) come verbatim from the Service function signature:
the type of the `@Body` parameter and the declared return type (wrappers like `Response<T>` / `Call<T>` kept as written).
"-" when there is no `@Body` or no declared return type. Each is backed by an Evidence row.

**Broken Paths** lists every chain that starts at a Service function but does not reach a Fragment.
Only proven cells are filled (everything else is "-"); each row says which layer it stopped at,
the missing link, and any related Unresolved entry. Complete chains stay in the matrix; a Service
function can appear in both when one path is complete and another dead-ends.
Repository suffixes: Repo, Repository, RepoImpl, RepositoryImpl (exact, case-sensitive).
UseCase suffixes: UseCase and Usecase (exact, case-sensitive, so `GetUserUsecase.kt` is accepted but `GetUserusecase.kt` is not).
Fully qualified injected types (`private val userUseCase: com.example.UserUseCase`, in a constructor, a property or `@Inject lateinit var`) are resolved by their package: only a class named `UserUseCase` declared in `package com.example` matches. If no such class is among the filtered files, the binding is logged as Unresolved instead of falling back to another `UserUseCase`.
Folder exclusions (test/, androidTest/, build/, generated/, ...) only apply to folders above the source root (`src/<set>/java/` or `src/<set>/kotlin/`). Package folders below it are never excluded, so `package scan.test` in `src/main/java/scan/test/` is analyzed, while `src/test/java/...` is still skipped.
Files whose name contains `mock` anywhere (case-insensitive, e.g. `MockUserService.kt`, `UserMockService.kt`, `UserServiceMock.kt`) are skipped and listed on the console and the "Skipped Files" sheet. Only the file name is checked, not the folder or the class name inside.
Supported chains: A Service>UseCase>Repository>ViewModel>Fragment, B Service>UseCase>ViewModel>Fragment, C Service>Repository>ViewModel>Fragment, D Service>Repository>UseCase>ViewModel>Fragment, E Service>UseCase>Fragment/Activity (the screen calls the UseCase directly, no Repository or ViewModel; ViewModel columns are "-").
In A the Repository calls the UseCase; in D the UseCase calls the Repository. For D, "ViewModel Function Source Name" is the UseCase.

ViewModel → UseCase links are found by looking for the UseCase class name in the ViewModel's constructor
or properties, then for a call through that name. Three call shapes are linked, each with an Evidence row:
`getUserUseCase.invoke(id)` / `getUserUseCase.execute(id)` (dot call), `getUserUseCase(id)` (operator invoke, only when
the UseCase declares `operator fun invoke`), and a class-level alias such as `private val getUser = getUserUseCase`
followed by `getUser(id)`. If the alias name is also one of the ViewModel's own functions, the call is logged as
Ambiguous binding instead of linked.

`tests/fixture` is a synthetic Android project that exercises all three patterns, const/concat/@Url URL resolution and the private→override repository walk-up:

```
python3 kt_traceability.py --root tests/fixture --out /tmp/fixture.xlsx
```

## Mock samples

`samples/shop-app` is a mock Android project with known answers. It covers:

| Case | Where |
|---|---|
| Pattern A, private → private → `override` walk-up | ProductService → GetProductsUseCase → ProductRepoImpl → CatalogViewModel → CatalogFragment |
| Pattern B, `by activityViewModels()`, Koin `by inject()`, fan-out to 2 Fragments | CartService → GetCartUseCase / RemoveCartItemUseCase → CartViewModel → CartFragment, CheckoutFragment |
| Pattern C, `@Inject lateinit var` | ProfileService → ProfileRepository → ProfileViewModel → ProfileFragment |
| Pattern D, alias + operator invoke, private → suspend walk-up | OrderService → OrderRepository → GetOrdersUseCase → OrderViewModel → OrderFragment |
| URL: literal, imported const, `Object.CONST`, companion const, `BASE + PRODUCTS`, `@HTTP(path=)`, `@Url`, missing const | ProductService, CartService, ProfileService |
| Private → plain public `fun` walk-up | ProfileRepository.pushUpdate → saveProfile → ProfileViewModel.save → ProfileFragment |
| Ambiguous binding (2 impls of one interface) | PaymentRepo ← PaymentRepoImpl, FakePaymentRepoImpl |
| ViewModel used by an Activity (shown in the Fragment columns) | ProfileService → ProfileRepository → SettingsViewModel → SettingsActivity |
| Step 0 exclusions | ProductRepoHelper, Legacyservice, files under test/, androidTest/, build/generated/ |

Expected results are in `expected_matrix.csv`, `expected_broken.csv`, `expected_files.csv` and `expected_unresolved.csv`. To test:

```
python3 kt_traceability.py --root samples/shop-app --out shop.xlsx
python3 check_expected.py --xlsx shop.xlsx --sample samples/shop-app
```

Other single-case samples live in `samples/` with their output in `results/<name>/`. `usecase-invoke-alias` and
`usecase-invoke-hilt` are the two ViewModel styles from the UseCase reference (plain constructor + alias, and
`@HiltViewModel` + direct invoke). Both link GetUserUseCase.invoke → UserViewModel.loadUser (Pattern B) and stop
at ViewModel because no Fragment is included.

When two classes share a simple name (for example `UserService` in two modules), the injected type is resolved
the way Kotlin does it: explicit import, then same package, then wildcard import. The choice gets a
"Type resolved by ..." Evidence row. If none of these proves one class, the binding is logged as Ambiguous
binding and not linked. See `samples/duplicate-service-name`.

Repository walk-up: a private function is never reported. The analyzer walks up to the first non-private
function in the same class that calls it (public, internal or protected, suspend or not), with a
"Private -> entry walk-up" Evidence row. If only private functions reach it, it is logged as "No public entry"
(`samples/private-only-no-entry`).

ViewModel properties count as ViewModel functions when their initializer, `by lazy { }` or getter makes a call,
e.g. `val authenticationResult: LiveData<...> = authToken.let { getAuthenticationUseCase.execute(it) }`. The
property name goes in "ViewModel Function", and a Fragment reading it (`vm.authenticationResult.observe(...)`) is
linked as "Property read". See `samples/viewmodel-property-usecase`.

Activities are linked to ViewModels the same way Fragments are and appear in the "Fragment Name" / "Fragment
Function" columns. An Activity's ViewModel can come from `by viewModels()`, `by viewModel()` (Koin),
`ViewModelProvider(this).get(X::class.java)` or `[X::class.java]`, or a typed `lateinit var`. See
`samples/activity-observes-viewmodel`.
