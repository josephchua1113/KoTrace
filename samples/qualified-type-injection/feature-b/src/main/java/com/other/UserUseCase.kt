package com.other

// same simple name as com.example.UserUseCase; calls the Service directly
class UserUseCase(private val service: com.other.UserService) {
    suspend fun execute(id: String) = service.getUser(id)
}
