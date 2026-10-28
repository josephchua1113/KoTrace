package com.demo

interface UserRepository {
 suspend fun getAuthentication(token: String): Result<AuthResponse>
}
