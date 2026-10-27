class GetUserUseCase(
    private val userService: UserService
) {

    suspend operator fun invoke(
        userId: String
    ): Result<UserResponse> {

        return try {
            val response = userService.getUser(userId)

            if (response.isSuccessful) {
                response.body()?.let {
                    Result.success(it)
                } ?: Result.failure(
                    Exception("Empty response body")
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
}
