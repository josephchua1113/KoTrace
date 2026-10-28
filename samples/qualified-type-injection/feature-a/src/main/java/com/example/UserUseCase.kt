package com.example

class UserUseCase(private val repository: com.example.UserRepository) {
    suspend fun execute(id: String) = repository.loadUser(id)
}
