class UserRepository {

    suspend fun getUserName(userId: String): String {
        // Network/API call
        kotlinx.coroutines.delay(1000)

        return formatUserName("john doe")
    }

    private fun formatUserName(name: String): String {
        return name.uppercase()
    }
}
