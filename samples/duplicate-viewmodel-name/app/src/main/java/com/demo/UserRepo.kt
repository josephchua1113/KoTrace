package com.demo
class UserRepo(private val service: UserService) {
    suspend fun users() = service.getUsers()
    suspend fun profile() = service.getProfile()
}
