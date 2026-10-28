package com.demo

class UserRepositoryImpl(
    private val service: UserService
) : UserRepository {

    override suspend fun getAuthentication(
        token: String
    ): Result<AuthResponse> {

        val response = service.getAuth(token)

        return if (response.isSuccessful) {
            Result.success(response.body()!!)
        } else {
            Result.failure(Exception("API Error"))
        }
    }
}
