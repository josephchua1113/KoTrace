package com.demo
class ProfileViewModel(private val repo: UserRepo) : ViewModel() {
    fun load() { viewModelScope.launch { repo.profile() } }
}
