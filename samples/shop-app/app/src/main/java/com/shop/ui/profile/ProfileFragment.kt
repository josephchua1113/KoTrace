package com.shop.ui.profile

import android.os.Bundle
import android.view.View
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels

class ProfileFragment : Fragment() {

    private val profileViewModel: ProfileViewModel by viewModels()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        profileViewModel.loadProfile()
        binding.saveButton.setOnClickListener { profileViewModel.save(currentProfile()) }
    }

    private fun currentProfile(): Profile = Profile("me")
}
