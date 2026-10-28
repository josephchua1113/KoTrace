package scan.app

// package does not match: UserUseCase lives in scan.test, not scan.testing -> Unresolved
class SettingsViewModel(
    private val userUseCase: scan.testing.UserUseCase
) : ViewModel() {
    fun refresh(id: String) {
        viewModelScope.launch { userUseCase.execute(id) }
    }
}
