package com.demo
import javax.inject.Inject
class StatsRepository @Inject constructor(private val statsApi: StatsService) {
    suspend fun fetchStats(): Stats = statsApi.getStats()
}
