class UserRepository(
    private val service: UserService
) {

    suspend fun getDisplayName(userId: String): String {

        val user = service.getUser(userId)

        return buildDisplayName(user)
    }

    private fun buildDisplayName(user: User): String {
        return "[${user.id}] ${user.name.uppercase()}"
    }
}
