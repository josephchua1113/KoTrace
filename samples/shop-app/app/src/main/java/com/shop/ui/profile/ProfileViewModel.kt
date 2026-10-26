package com.shop.ui.profile

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.shop.data.repo.ProfileRepository
import kotlinx.coroutines.launch
import javax.inject.Inject

class ProfileViewModel @Inject constructor(
    private val profileRepository: ProfileRepository
) : ViewModel() {

    fun loadProfile() = viewModelScope.launch { profileRepository.getProfile() }

    fun save(profile: Profile) {
        profileRepository.saveProfile(profile)
    }
}
