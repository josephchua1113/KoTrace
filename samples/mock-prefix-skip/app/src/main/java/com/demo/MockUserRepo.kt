package com.demo

class MockUserRepo(private val service: UserService) {
    suspend fun fake(userId: String) = service.getUser(userId)
}
