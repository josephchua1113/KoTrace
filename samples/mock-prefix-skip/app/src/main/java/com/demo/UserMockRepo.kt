package com.demo

class UserMockRepo(private val service: UserService) {
    suspend fun load(userId: String) = service.getUser(userId)
}
