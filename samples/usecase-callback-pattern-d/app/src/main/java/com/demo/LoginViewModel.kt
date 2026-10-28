package com.demo

class LoginViewModel(
    private val getAuthenticationUseCase: GetAuthenticationUseCase
) : ViewModel() {

    fun authenticate(token: String): LiveData<Event<ResultWithData<Response>>> {
        return getAuthenticationUseCase.execute(token)
    }
}
