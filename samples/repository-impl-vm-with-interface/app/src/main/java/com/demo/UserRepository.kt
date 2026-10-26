// ADDED FOR THIS RUN ONLY: the interface the ViewModel injects (not in the original mock)
interface UserRepository {
    suspend fun getUserDisplayName(userId: String): String
}
