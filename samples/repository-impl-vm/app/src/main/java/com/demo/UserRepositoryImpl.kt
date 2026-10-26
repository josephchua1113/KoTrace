class UserRepositoryImpl(
    private val service: UserService
) : UserRepository {

    override suspend fun getUserDisplayName(
        userId: String
    ): String {

        return loadAndFormatUser(userId)
    }

    private suspend fun loadAndFormatUser(
        userId: String
    ): String {

        val response = service.getUser(
            UserRequest(
                userId = userId
            )
        )

        return "${response.id} - ${response.name.uppercase()}"
    }
}
