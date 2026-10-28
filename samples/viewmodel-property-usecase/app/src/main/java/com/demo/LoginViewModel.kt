package com.demo

class LoginViewModel(
    private val getAuthenticationUseCase: GetAuthenticationUseCase,
    private val authToken: String
) : ViewModel() {

    val authenticationResult: LiveData<Event<ResultWithData<Response>>> =
        authToken.let {
            getAuthenticationUseCase.execute(it)
        }
}
