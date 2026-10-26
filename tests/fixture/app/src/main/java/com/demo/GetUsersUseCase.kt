package com.demo
import javax.inject.Inject
class GetUsersUseCase @Inject constructor(private val api: UserService) {
    suspend fun execute(): List<User> = api.getUsers()
}
