package com.demo

class FakeUserService : UserService {
    override suspend fun getUser(userId: String): Response<UserResponse> = Response.success(UserResponse())
}
