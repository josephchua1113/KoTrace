class UserViewModel(
private val repository: UserRepository
) : ViewModel() {
 
private val _userName = MutableStateFlow("")
val userName: StateFlow<String> = _userName
 
fun loadUser(userId: String) {
 
viewModelScope.launch {
 
try {
 
val result =
repository.getUserDisplayName(userId)
 
_userName.value = result
 
} catch (e: Exception) {
 
_userName.value =
"Failed: ${e.message}"
}
}
}
}
