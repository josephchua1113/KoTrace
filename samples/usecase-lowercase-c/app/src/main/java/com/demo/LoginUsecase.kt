package com.demo

class LoginUsecase(private val service: UserService) {
    suspend operator fun invoke(token: String) = service.getAuth(token)
}
