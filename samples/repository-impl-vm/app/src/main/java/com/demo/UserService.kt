interface UserService {

    @POST("v1/user/details")
    suspend fun getUser(
        @Body request: UserRequest
    ): UserResponse
}
