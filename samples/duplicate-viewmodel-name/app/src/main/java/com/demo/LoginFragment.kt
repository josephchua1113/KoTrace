package com.demo
class LoginFragment : Fragment() {
    private val loginViewModel: LoginViewModel by viewModels()
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) { loginViewModel.load() }
}
