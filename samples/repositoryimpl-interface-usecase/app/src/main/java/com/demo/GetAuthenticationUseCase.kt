package com.demo

class GetAuthenticationUseCase(
    private val repository: UserRepository
) {

    suspend fun execute(
        token: String
    ): Result<AuthResponse> {
        return repository.getAuthentication(token)
    }
}
