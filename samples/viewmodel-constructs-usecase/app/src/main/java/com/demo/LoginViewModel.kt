package com.demo

class LoginViewModel : ViewModel() {
    private val getAuthenticationUseCase = GetAuthenticationUseCase(UserRepo(ApiClient.service))
    fun authenticate(t: String) = getAuthenticationUseCase.execute(t)
}
