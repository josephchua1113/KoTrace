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

    // public but neither override nor suspend: the private call below has no valid entry
    fun saveProfile(profile: Profile) {
        CoroutineScope(Dispatchers.IO).launch { pushUpdate(profile) }
    }

    private suspend fun pushUpdate(profile: Profile) = profileService.updateProfile(profile)
}
