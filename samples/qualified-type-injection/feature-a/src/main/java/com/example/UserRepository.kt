package com.example

// Service injected with a fully qualified type
class UserRepository(private val service: com.example.UserService) {
    suspend fun loadUser(id: String) = service.getUser(id)
}
