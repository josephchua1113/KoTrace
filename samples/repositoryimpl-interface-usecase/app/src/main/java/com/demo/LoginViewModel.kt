package com.demo

class LoginViewModel(
    private val getAuthenticationUseCase: GetAuthenticationUseCase
) : ViewModel() {

    fun login(token: String) {
        viewModelScope.launch {
            getAuthenticationUseCase.execute(token)
        }
    }
}
