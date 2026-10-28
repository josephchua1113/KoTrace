package com.demo

@AndroidEntryPoint
class LoginActivity : AppCompatActivity() {

    @Inject
    lateinit var getAuthenticationUseCase: GetAuthenticationUseCase

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        lifecycleScope.launch {
            getAuthenticationUseCase("token")
        }
    }
}
