class UserViewModel(
getUserUseCase: GetUserUseCase
) : ViewModel() {
 
// Store use case as a val
private val getUser = getUserUseCase
 
private val _uiState =
MutableStateFlow<UserUiState>(UserUiState.Loading)
 
val uiState: StateFlow<UserUiState> =
_uiState.asStateFlow()
 
fun loadUser(userId: String) {
viewModelScope.launch {
 
_uiState.value = UserUiState.Loading
 
getUser(userId)
.onSuccess { user ->
_uiState.value = UserUiState.Success(user)
}
.onFailure { error ->
_uiState.value = UserUiState.Error(
error.message ?: "Unknown error"
)
}
}
}
}
