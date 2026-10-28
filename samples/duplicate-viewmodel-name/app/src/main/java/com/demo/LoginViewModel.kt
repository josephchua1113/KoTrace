package com.demo
class LoginViewModel(private val repo: UserRepo) : ViewModel() {
    fun load() { viewModelScope.launch { repo.users() } }
}
