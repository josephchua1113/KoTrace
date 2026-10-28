package com.demo

class GetUserUseCase @Inject constructor(
    private val service: UserService
) {
    suspend fun execute(id: String): Response<UserResponse> {
        return service.getUser(id)
    }
}
