package com.demo

class GetAuthenticationUseCase(
    private val repository: UserRepo
) : CoroutineScope,
    BaseUseCase<String, LiveData<Event<ResultWithData<Response>>>> {

    override val coroutineContext: CoroutineContext
        get() = Dispatchers.IO + SupervisorJob()

    override fun execute(
        param: String
    ): LiveData<Event<ResultWithData<Response>>> {

        val result = MutableLiveData<Event<ResultWithData<Response>>>()

        launch {

            try {

                repository.getAuthentication(
                    cbOnResult = { response ->

                        result.postValue(
                            Event(
                                ResultWithData.success(response)
                            )
                        )
                    },
                    cbOnError = { error ->

                        result.postValue(
                            Event(
                                ResultWithData.error(
                                    error.message ?: "Unknown Error"
                                )
                            )
                        )
                    }
                )

            } catch (e: Exception) {

                result.postValue(
                    Event(
                        ResultWithData.error(
                            e.message ?: "Unexpected Error"
                        )
                    )
                )
            }
        }

        return result
    }
}
