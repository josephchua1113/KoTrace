package com.demo

class UserRepo(
    private val service: UserService
) {

    private fun getAuthAPI(): Call<AuthResponse> {
        return service.getAuth()
    }

    fun getAuthentication(
        cbOnResult: (AuthResponse?) -> Unit,
        cbOnError: (Throwable) -> Unit
    ) {

        getAuthAPI().enqueue(
            { res ->

                val response = res.body()

                if (response?.status?.first == true) {
                    cbOnResult(response)
                } else {
                    cbOnError(
                        Exception("Authentication failed")
                    )
                }
            },
            { error ->
                cbOnError(error)
            }
        )
    }
}
