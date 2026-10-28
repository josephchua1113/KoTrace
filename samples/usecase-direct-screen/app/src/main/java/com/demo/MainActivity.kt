package com.demo

class MainActivity : AppCompatActivity() {

    private val getUserUseCase: GetUserUseCase by inject()

    override fun onResume() {
        super.onResume()
        lifecycleScope.launch { getUserUseCase.execute("me") }
    }
}
