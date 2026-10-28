package com.other
import com.demo.UserRepo
class LoginViewModel(private val repo: UserRepo) : ViewModel() {
    fun load() { viewModelScope.launch { repo.profile() } }
}
