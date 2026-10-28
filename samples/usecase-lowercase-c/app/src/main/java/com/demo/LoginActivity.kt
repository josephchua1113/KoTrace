package com.demo

class LoginActivity : AppCompatActivity() {
    @Inject
    lateinit var loginUsecase: LoginUsecase

    override fun onCreate(savedInstanceState: Bundle?) {
        lifecycleScope.launch { loginUsecase("token") }
    }
}
