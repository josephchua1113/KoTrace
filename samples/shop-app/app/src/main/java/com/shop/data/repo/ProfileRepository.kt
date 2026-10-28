package com.shop.data.repo

import com.shop.data.remote.ProfileService
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import javax.inject.Inject

class ProfileRepository @Inject constructor() {

    // field injection
    @Inject lateinit var profileService: ProfileService

    suspend fun getProfile(): Profile = profileService.getProfile()

    // public plain fun: the private call below walks up to this entry
    fun saveProfile(profile: Profile) {
        CoroutineScope(Dispatchers.IO).launch { pushUpdate(profile) }
    }

    private suspend fun pushUpdate(profile: Profile) = profileService.updateProfile(profile)
}
