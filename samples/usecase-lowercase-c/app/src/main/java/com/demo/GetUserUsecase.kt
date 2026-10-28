package com.demo

// "Usecase" (lowercase c) is accepted as a UseCase suffix
class GetUserUsecase @Inject constructor(private val service: UserService) {
    suspend fun execute(id: String) = service.getUser(id)
}
