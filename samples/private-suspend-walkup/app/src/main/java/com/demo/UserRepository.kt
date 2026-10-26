class UserRepository(
    private val service: UserService
) {

    suspend fun getUserDisplayName(
        userId: String
    ): String {

        return loadAndFormatUser(userId)
    }

    private suspend fun loadAndFormatUser(
        userId: String
    ): String {

        val response = service.getUser(
            UserRequest(userId)
        )

        return "${response.id} - ${response.name.uppercase()}"
    }
}
