package com.demo

@AndroidEntryPoint
class ProfileFragment : Fragment() {

    @Inject
    lateinit var getUserUseCase: GetUserUseCase

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewLifecycleOwner.lifecycleScope.launch {
            val user = getUserUseCase.execute("42")
        }
    }
}
