package com.demo
import javax.inject.Inject
class UserRepoImpl @Inject constructor(
    private val useCase: GetUsersUseCase
) : UserRepo {
    override suspend fun loadUsers(): List<User> {
        return fetchInternal()
    }
    private suspend fun fetchInternal(): List<User> {
        return hop()
    }
    private suspend fun hop(): List<User> = useCase.execute()
}
