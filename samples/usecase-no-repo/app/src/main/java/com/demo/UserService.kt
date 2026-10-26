interface UserService {

    suspend fun getUser(userId: String): User

    companion object {
        const val BASE_URL = "https://api.example.com/"
    }
}
