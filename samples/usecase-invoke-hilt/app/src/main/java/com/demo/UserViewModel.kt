@HiltViewModel
class UserViewModel @Inject constructor(
private val getUserUseCase: GetUserUseCase
) : ViewModel() {
 
fun loadUser(userId: String) {
viewModelScope.launch {
val result = getUserUseCase(userId)
 
result.onSuccess {
// handle success
}.onFailure {
// handle error
}
}
}
}
