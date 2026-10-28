package com.demo

@HiltViewModel
class ProfileViewModel @Inject constructor(
    private val getUserUsecase: GetUserUsecase
) : ViewModel() {
    fun load(id: String) {
        viewModelScope.launch { getUserUsecase.execute(id) }
    }
}
