package com.demo

class LoginActivity : AppCompatActivity() {

    private val viewModel: LoginViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        initScreen()
    }

    private fun initScreen(){
        viewModel.authenticationResult().observe(this, authBbserver)
    }

    private val authObserver = Observe<ResultWithData<Response>> {
        if(it.Success) -> {
        }
    }
}
