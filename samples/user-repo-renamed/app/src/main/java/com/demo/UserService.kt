interface UserService {

    @POST("user/details")
    suspend fun getUser(
        @Body request: UserRequest
    ): UserResponse

    companion object {
        const val BASE_URL = "https://api.example.com/"
    }
}
