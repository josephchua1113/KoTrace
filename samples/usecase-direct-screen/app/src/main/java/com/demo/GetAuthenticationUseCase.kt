package com.demo

class GetAuthenticationUseCase @Inject constructor(
    private val service: UserService
) {
    suspend operator fun invoke(token: String) = service.getAuth(token)
}
