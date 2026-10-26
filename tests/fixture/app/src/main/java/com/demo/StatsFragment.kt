package com.demo
import androidx.fragment.app.Fragment
class StatsFragment : Fragment() {
    private val statsVm: StatsViewModel by viewModels()
    override fun onResume() {
        statsVm.loadStats()
    }
}
