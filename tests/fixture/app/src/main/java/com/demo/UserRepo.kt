package com.demo
interface UserRepo {
    suspend fun loadUsers(): List<User>
}
