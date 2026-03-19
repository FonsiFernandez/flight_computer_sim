class StatusRenderer:
    def __init__(self, health_status_text_resolver):
        self.health_status_text_resolver = health_status_text_resolver

    def build_status_text(
        self,
        latest_frame,
        stopped: bool,
        paused: bool,
        replay_mode: bool,
        replay_label: str,
        event_log_path
    ) -> str:
        if latest_frame is None:
            return "WAITING FOR TELEMETRY..."

        lf = latest_frame
        status_text = self.health_status_text_resolver(lf.health_status)
        execution_state = "STOPPED" if stopped else ("PAUSED" if paused else "RUNNING")

        return (
            f"MODE:            {lf.mode}\n"
            f"EXECUTION:       {execution_state}\n"
            f"PHASE:           {lf.mission_phase}\n"
            f"TIME:            {lf.time_ms / 1000.0:.1f} s\n\n"

            f"TRUTH LAT:       {lf.truth_lat_deg:.6f} deg\n"
            f"TRUTH LON:       {lf.truth_lon_deg:.6f} deg\n"
            f"TRUTH ALT:       {lf.truth_altitude_m:.2f} m\n"
            f"TRUTH VEL Z:     {lf.truth_velocity_z_mps:.2f} m/s\n"
            f"TRUTH ACCEL Z:   {lf.truth_acceleration_z_mps2:.2f} m/s²\n"
            f"TRUTH PITCH:     {lf.truth_pitch_deg:.2f} deg\n"
            f"TRUTH PITCH RT:  {lf.truth_pitch_rate_dps:.2f} dps\n\n"

            f"GPS LAT:         {lf.gps_lat_deg:.6f} deg\n"
            f"GPS LON:         {lf.gps_lon_deg:.6f} deg\n"
            f"GPS ALT:         {lf.gps_altitude_m:.2f} m\n"
            f"GPS V_NORTH:     {lf.gps_velocity_north_mps:.2f} m/s\n"
            f"GPS V_EAST:      {lf.gps_velocity_east_mps:.2f} m/s\n"
            f"GPS FIX:         {lf.gps_fix_valid}\n\n"

            f"MEAS ALT:        {lf.altitude_m:.2f} m\n"
            f"MEAS ACCEL Z:    {lf.az:.2f} m/s²\n"
            f"GYRO Z:          {lf.gyro_z_dps:.2f} dps\n"
            f"ALT ERROR:       {lf.altitude_m - lf.truth_altitude_m:.2f} m\n"
            f"ACCEL ERROR:     {lf.az - lf.truth_acceleration_z_mps2:.2f} m/s²\n\n"

            f"BATTERY:         {lf.battery_voltage_v:.2f} V\n"
            f"TEMP:            {lf.board_temp_c:.2f} °C\n"
            f"HK VALID:        {lf.hk_valid}\n\n"

            f"IMU VALID:       {lf.imu_valid}\n"
            f"ALT VALID:       {lf.alt_valid}\n"
            f"HEALTH:          {status_text}\n\n"

            f"IMU FAULT CNT:   {lf.imu_fault_count}\n"
            f"IMU REC CNT:     {lf.imu_recovery_count}\n"
            f"ALT FAULT CNT:   {lf.alt_fault_count}\n"
            f"ALT REC CNT:     {lf.alt_recovery_count}\n\n"

            f"IMU LATCHED:     {lf.imu_latched}\n"
            f"ALT LATCHED:     {lf.alt_latched}\n\n"

            f"REPLAY FRAME:    {replay_label if replay_mode else 'LIVE'}\n"
            f"EVENT LOG FILE:  {event_log_path.name if event_log_path else 'n/a'}\n"
        )

    @staticmethod
    def apply_text_preserving_scroll(text_edit, new_text: str):
        if text_edit.toPlainText() == new_text:
            return

        scrollbar = text_edit.verticalScrollBar()
        old_value = scrollbar.value()
        at_bottom = old_value == scrollbar.maximum()

        text_edit.blockSignals(True)
        text_edit.setPlainText(new_text)
        text_edit.blockSignals(False)

        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(min(old_value, scrollbar.maximum()))