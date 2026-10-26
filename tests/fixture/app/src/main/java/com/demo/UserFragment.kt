package com.demo
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
class UserFragment : Fragment() {
    private val vm: UserViewModel by viewModels()
    override fun onViewCreated(v: View, s: Bundle?) {
        vm.refreshUsers()
    }
}
