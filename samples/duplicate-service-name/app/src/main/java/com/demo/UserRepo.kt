package com.demo.data
import com.demo.UserService
class UserRepo constructor(
    private val service: UserService
) {

    suspend fun doregister(
        userId: String
    ): Result<UserResponse> {

        return try {
            val response = fetchUserAPI(userId)

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

    private fun fetchUserAPI(
        userId: String
    ): Response<UserResponse> {
        return service.getUser(userId)
    }
}
