package com.shop.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.shop.data.repo.ProfileRepository
import kotlinx.coroutines.launch
import javax.inject.Inject

class SettingsViewModel @Inject constructor(
    private val profileRepository: ProfileRepository
) : ViewModel() {
    fun loadSettings() {
        viewModelScope.launch { profileRepository.getProfile() }
    }
}
