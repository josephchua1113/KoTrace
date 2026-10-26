package com.demo
import com.demo.ApiPaths.USER_DETAILS
import retrofit2.http.*
interface UserService {
    @GET("v1/users")
    suspend fun getUsers(): List<User>

    @GET(USER_DETAILS)
    suspend fun getUserDetails(@Query("id") id: String): User

    @POST(ApiPaths.BASE + "/create")
    suspend fun createUser(@Body u: User): User

    @GET
    suspend fun download(@Url url: String): String

    @GET(MISSING_CONST)
    suspend fun broken(): String
}
