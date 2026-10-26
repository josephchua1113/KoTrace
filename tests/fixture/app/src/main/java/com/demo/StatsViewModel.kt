package com.demo
import androidx.lifecycle.ViewModel
import javax.inject.Inject
class StatsViewModel @Inject constructor(private val statsRepo: StatsRepository) : ViewModel() {
    fun loadStats() {
        viewModelScope.launch { statsRepo.fetchStats() }
    }
}
