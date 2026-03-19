class TileRenderer:
    def __init__(
        self,
        health_status_text_resolver,
        mode_color_resolver,
        health_color_resolver,
        execution_color_resolver
    ):
        self.health_status_text_resolver = health_status_text_resolver
        self.mode_color_resolver = mode_color_resolver
        self.health_color_resolver = health_color_resolver
        self.execution_color_resolver = execution_color_resolver

    def render(
        self,
        latest_frame,
        stopped: bool,
        paused: bool,
        tile_mode,
        tile_phase,
        tile_health,
        tile_execution,
        tile_gps,
        tile_battery,
        tile_temp
    ):
        if latest_frame is None:
            tile_mode.set_value("--")
            tile_phase.set_value("--")
            tile_health.set_value("--")
            tile_execution.set_value("IDLE")
            tile_gps.set_value("--")
            tile_battery.set_value("--")
            tile_temp.set_value("--")

            for tile in [
                tile_mode,
                tile_phase,
                tile_health,
                tile_execution,
                tile_gps,
                tile_battery,
                tile_temp
            ]:
                tile.set_color("#7f8c9a")
            return

        lf = latest_frame
        execution_state = "STOPPED" if stopped else ("PAUSED" if paused else "RUNNING")
        health_text = self.health_status_text_resolver(lf.health_status)

        tile_mode.set_value(lf.mode)
        tile_phase.set_value(lf.mission_phase)
        tile_health.set_value(health_text)
        tile_execution.set_value(execution_state)

        tile_mode.set_color(self.mode_color_resolver(lf.mode))
        tile_phase.set_color("#7fb3ff")
        tile_health.set_color(self.health_color_resolver(lf.health_status))
        tile_execution.set_color(self.execution_color_resolver(execution_state))

        gps_text = "OK" if lf.gps_fix_valid else "NO FIX"
        tile_gps.set_value(gps_text)
        tile_gps.set_color("#33d17a" if lf.gps_fix_valid else "#ff5c5c")

        tile_battery.set_value(f"{lf.battery_voltage_v:.2f} V")
        tile_battery.set_color("#33d17a" if lf.battery_voltage_v > 14 else "#ffb347")

        tile_temp.set_value(f"{lf.board_temp_c:.1f} °C")
        tile_temp.set_color("#33d17a" if lf.board_temp_c < 50 else "#ff5c5c")