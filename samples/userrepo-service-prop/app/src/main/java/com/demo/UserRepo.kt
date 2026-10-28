package com.demo

class UserRepo(
    private val service: UserService
) {

    suspend fun getUser(
        userId: String
    ): Result<UserResponse> {

        return try {
            val response = fetchUser(userId)

            if (response.isSuccessful) {
                response.body()?.let {
                    Result.success(it)
                } ?: Result.failure(
                    Exception("Empty response")
                )
            } else {
                Result.failure(
                    Exception("API Error: ${response.code()}")
                )
            }

        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private suspend fun fetchUser(
        userId: String
    ): Response<UserResponse> {
        return service.getUser(userId)
    }
}
