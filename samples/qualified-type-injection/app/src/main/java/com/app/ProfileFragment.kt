package com.app

class ProfileFragment : Fragment() {
    private val viewModel: com.app.ProfileViewModel by viewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        viewModel.load("42")
    }
}
