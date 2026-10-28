package com.app

class AdminActivity : AppCompatActivity() {
    private val viewModel: AdminViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        viewModel.loadAdmin("1")
    }
}
