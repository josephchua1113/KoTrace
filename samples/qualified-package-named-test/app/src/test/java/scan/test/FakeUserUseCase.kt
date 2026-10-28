package scan.test

// real test source set (src/test) -> still excluded
class FakeUserUseCase(private val service: UserService) {
    suspend fun execute(id: String) = service.getUser(id)
}
