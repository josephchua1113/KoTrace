# kt-traceability

Deterministic Service → Fragment traceability matrix for Kotlin/Android codebases.
Every link is backed by file path, line and symbol; anything unprovable is "-" and logged in the Unresolved sheet.

```
pip install openpyxl
python3 kt_traceability.py --root /path/to/android/project --out traceability_matrix.xlsx
```

Sheets: Traceability Matrix, Broken Paths, Evidence, Unresolved, plus Filtered Files and Service Endpoints for review.

**Broken Paths** lists every chain that starts at a Service function but does not reach a Fragment.
Only proven cells are filled (everything else is "-"); each row says which layer it stopped at,
the missing link, and any related Unresolved entry. Complete chains stay in the matrix; a Service
function can appear in both when one path is complete and another dead-ends.
Supported chains: A Service>UseCase>Repository>ViewModel>Fragment, B Service>UseCase>ViewModel>Fragment, C Service>Repository>ViewModel>Fragment.

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
| URL: literal, imported const, `Object.CONST`, companion const, `BASE + PRODUCTS`, `@HTTP(path=)`, `@Url`, missing const | ProductService, CartService, ProfileService |
| No override/suspend entry | ProfileRepository.pushUpdate ← saveProfile (plain `fun`) |
| Ambiguous binding (2 impls of one interface) | PaymentRepo ← PaymentRepoImpl, FakePaymentRepoImpl |
| ViewModel used only by an Activity | SettingsViewModel ← SettingsActivity |
| Step 0 exclusions | ProductRepoHelper, ProductRepositoryImpl, Legacyservice, files under test/, androidTest/, build/generated/ |

Expected results are in `expected_matrix.csv`, `expected_broken.csv`, `expected_files.csv` and `expected_unresolved.csv`. To test:

```
python3 kt_traceability.py --root samples/shop-app --out shop.xlsx
python3 check_expected.py --xlsx shop.xlsx --sample samples/shop-app
```
