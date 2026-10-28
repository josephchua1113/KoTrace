package com.app

// qualified type points at a package with no UserUseCase -> Unresolved, never guessed
class BrokenViewModel(
    private val userUseCase: com.missing.UserUseCase
) : ViewModel() {
    fun load(id: String) {
        viewModelScope.launch { userUseCase.execute(id) }
    }
}
