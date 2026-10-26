interface UserService {

    @GET("users/{id}")
    suspend fun getUser(
        @Path("id") userId: String
    ): User
}
