package scan.test

// package scan.test: the "test" folder here is a package folder, not the test source set
class UserUseCase(private val service: UserService) {
    suspend fun execute(id: String) = service.getUser(id)
}
