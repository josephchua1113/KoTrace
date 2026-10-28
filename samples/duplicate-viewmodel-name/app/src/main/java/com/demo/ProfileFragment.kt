package com.demo
class ProfileFragment : Fragment() {
    private val vm: ProfileViewModel by viewModels()
    override fun onResume() { vm.load() }
}
