package com.app

// constructor parameter with a fully qualified type, no import
class ProfileViewModel(
    private val userUseCase: com.example.UserUseCase
) : ViewModel() {
    fun load(id: String) {
        viewModelScope.launch { userUseCase.execute(id) }
    }
}
