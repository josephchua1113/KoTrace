package scan.app

class ProfileViewModel(
    private val userUseCase: scan.test.UserUseCase
) : ViewModel() {
    fun load(id: String) {
        viewModelScope.launch { userUseCase.execute(id) }
    }
}
