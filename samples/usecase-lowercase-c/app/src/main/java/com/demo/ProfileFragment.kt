package com.demo

class ProfileFragment : Fragment() {
    private val viewModel: ProfileViewModel by viewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        viewModel.load("42")
    }
}
