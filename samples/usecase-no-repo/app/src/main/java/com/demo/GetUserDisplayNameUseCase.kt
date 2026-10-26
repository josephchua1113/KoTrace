class GetUserDisplayNameUseCase(
    private val repository: UserRepository
) {

    suspend operator fun invoke(
        userId: String
    ): String {

        return repository.getUserDisplayName(userId)
    }
}
