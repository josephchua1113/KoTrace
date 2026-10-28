package com.app

@HiltViewModel
class AdminViewModel : ViewModel() {

    // property injection with a fully qualified type
    @Inject
    lateinit var userUseCase: com.other.UserUseCase

    fun loadAdmin(id: String) {
        viewModelScope.launch { userUseCase.execute(id) }
    }
}
