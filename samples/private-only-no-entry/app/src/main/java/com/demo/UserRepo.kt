package com.demo

class UserRepo(private val service: UserService) {

    private fun getAuthAPI(): Call<AuthResponse> = service.getAuth()

    // private only: nothing outside the class can reach getAuthAPI
    private fun refresh() {
        getAuthAPI().execute()
    }
}
