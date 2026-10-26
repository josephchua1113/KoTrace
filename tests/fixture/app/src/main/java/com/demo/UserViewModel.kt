package com.demo
import androidx.lifecycle.ViewModel
import javax.inject.Inject
class UserViewModel @Inject constructor(private val repo: UserRepo) : ViewModel() {
    fun refreshUsers() {
        viewModelScope.launch { repo.loadUsers() }
    }
}
