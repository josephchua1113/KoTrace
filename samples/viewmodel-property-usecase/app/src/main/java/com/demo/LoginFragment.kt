package com.demo

class LoginFragment : Fragment() {

    private val loginViewModel: LoginViewModel by viewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        loginViewModel.authenticationResult.observe(viewLifecycleOwner) { event ->
            render(event)
        }
    }
}
