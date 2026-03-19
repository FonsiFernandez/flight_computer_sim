from matplotlib.image import imread


class PlotRenderer:
    def __init__(self, mode_color_resolver):
        self.mode_color_resolver = mode_color_resolver

    def draw_transition_lines(self, plot_widget, mode_transitions):
        if not mode_transitions:
            return

        for time_s, mode in mode_transitions:
            color = self.mode_color_resolver(mode)
            plot_widget.ax.axvline(
                time_s,
                color=color,
                linestyle="--",
                linewidth=1.0,
                alpha=0.55
            )

    def render_altitude_plot(self, plot_widget, buffer_data, auto_follow: bool):
        limits = None if auto_follow else plot_widget.get_axis_limits()

        plot_widget.clear(with_secondary=True)
        plot_widget.ax.set_title("ALTITUDE / TRUTH VS MEASURED")
        plot_widget.ax.set_xlabel("Time [s]")
        plot_widget.ax.set_ylabel("Altitude [m]")
        plot_widget.ax2.set_ylabel("Altitude Error [m]")

        if len(buffer_data.times) > 0:
            plot_widget.ax.plot(
                buffer_data.times,
                buffer_data.altitudes,
                linewidth=2.0,
                label="Measured Altitude"
            )
            plot_widget.ax.plot(
                buffer_data.times,
                buffer_data.truth_altitudes,
                linewidth=1.8,
                linestyle="--",
                label="Truth Altitude"
            )
            plot_widget.ax.plot(
                buffer_data.times,
                buffer_data.gps_altitudes,
                linewidth=1.5,
                linestyle=":",
                label="GPS Altitude"
            )
            plot_widget.ax2.plot(
                buffer_data.times,
                buffer_data.altitude_error,
                linewidth=1.3,
                linestyle=":",
                label="Altitude Error"
            )

        self.draw_transition_lines(plot_widget, buffer_data.mode_transitions)

        h1, l1 = plot_widget.ax.get_legend_handles_labels()
        h2, l2 = plot_widget.ax2.get_legend_handles_labels()
        if h1 or h2:
            plot_widget.ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)

        if not auto_follow:
            plot_widget.restore_axis_limits(limits)

        plot_widget.draw_idle_safe()

    def render_accel_plot(self, plot_widget, buffer_data, auto_follow: bool):
        limits = None if auto_follow else plot_widget.get_axis_limits()

        plot_widget.clear(with_secondary=True)
        plot_widget.ax.set_title("ACCEL Z / TRUTH VS MEASURED")
        plot_widget.ax.set_xlabel("Time [s]")
        plot_widget.ax.set_ylabel("Accel Z [m/s²]")
        plot_widget.ax2.set_ylabel("Accel Error [m/s²]")

        if len(buffer_data.times) > 0:
            plot_widget.ax.plot(
                buffer_data.times,
                buffer_data.accel_z,
                linewidth=2.0,
                label="Measured Accel Z"
            )
            plot_widget.ax.plot(
                buffer_data.times,
                buffer_data.truth_accel_z,
                linewidth=1.8,
                linestyle="--",
                label="Truth Accel Z"
            )
            plot_widget.ax2.plot(
                buffer_data.times,
                buffer_data.accel_z_error,
                linewidth=1.3,
                linestyle=":",
                label="Accel Error"
            )

        self.draw_transition_lines(plot_widget, buffer_data.mode_transitions)

        h1, l1 = plot_widget.ax.get_legend_handles_labels()
        h2, l2 = plot_widget.ax2.get_legend_handles_labels()
        if h1 or h2:
            plot_widget.ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)

        if not auto_follow:
            plot_widget.restore_axis_limits(limits)

        plot_widget.draw_idle_safe()

    def render_xy_plot(self, plot_widget, buffer_data, auto_follow: bool):
        limits = None if auto_follow else plot_widget.get_axis_limits()

        plot_widget.clear(with_secondary=True)
        plot_widget.ax.set_title("ACCEL X / Y + GYRO Z")
        plot_widget.ax.set_xlabel("Time [s]")
        plot_widget.ax.set_ylabel("Accel [m/s²]")
        plot_widget.ax2.set_ylabel("Gyro Z [dps]")

        if len(buffer_data.times) > 0:
            plot_widget.ax.plot(
                buffer_data.times,
                buffer_data.accel_x,
                linewidth=1.8,
                label="Accel X"
            )
            plot_widget.ax.plot(
                buffer_data.times,
                buffer_data.accel_y,
                linewidth=1.8,
                label="Accel Y"
            )
            plot_widget.ax2.plot(
                buffer_data.times,
                buffer_data.gyro_z,
                linewidth=1.5,
                linestyle="--",
                label="Gyro Z"
            )

        self.draw_transition_lines(plot_widget, buffer_data.mode_transitions)

        h1, l1 = plot_widget.ax.get_legend_handles_labels()
        h2, l2 = plot_widget.ax2.get_legend_handles_labels()
        if h1 or h2:
            plot_widget.ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)

        if not auto_follow:
            plot_widget.restore_axis_limits(limits)

        plot_widget.draw_idle_safe()

    def render_hk_plot(self, plot_widget, buffer_data, auto_follow: bool):
        limits = None if auto_follow else plot_widget.get_axis_limits()

        plot_widget.clear(with_secondary=True)
        plot_widget.ax.set_title("BATTERY / TEMPERATURE")
        plot_widget.ax.set_xlabel("Time [s]")
        plot_widget.ax.set_ylabel("Battery [V]")
        plot_widget.ax2.set_ylabel("Temperature [°C]")

        if len(buffer_data.times) > 0:
            plot_widget.ax.plot(
                buffer_data.times,
                buffer_data.battery_voltage,
                linewidth=1.8,
                label="Battery [V]"
            )
            plot_widget.ax2.plot(
                buffer_data.times,
                buffer_data.board_temp,
                linewidth=1.8,
                linestyle="--",
                label="Temp [°C]"
            )

        self.draw_transition_lines(plot_widget, buffer_data.mode_transitions)

        h1, l1 = plot_widget.ax.get_legend_handles_labels()
        h2, l2 = plot_widget.ax2.get_legend_handles_labels()
        if h1 or h2:
            plot_widget.ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)

        if not auto_follow:
            plot_widget.restore_axis_limits(limits)

        plot_widget.draw_idle_safe()

    def render_ground_track(
        self,
        plot_widget,
        buffer_data,
        latest_frame,
        auto_follow: bool,
        earth_map_path=None
    ):
        limits = None if auto_follow else plot_widget.get_axis_limits()

        plot_widget.clear(with_secondary=False)
        plot_widget.ax.set_title("GROUND TRACK / KOUROU REGION")
        plot_widget.ax.set_xlabel("Longitude [deg]")
        plot_widget.ax.set_ylabel("Latitude [deg]")

        earth_map_img = None
        if earth_map_path is not None:
            try:
                earth_map_img = imread(str(earth_map_path))
            except Exception:
                earth_map_img = None

        if earth_map_img is not None:
            plot_widget.ax.imshow(
                earth_map_img,
                extent=[-180, 180, -90, 90],
                aspect="auto",
                alpha=0.9,
                zorder=0
            )
        else:
            plot_widget.ax.text(
                0.5,
                0.5,
                "EARTH MAP NOT LOADED",
                transform=plot_widget.ax.transAxes,
                ha="center",
                va="center",
                fontsize=14,
                color="red"
            )

        if len(buffer_data.truth_lat) > 0:
            plot_widget.ax.plot(
                buffer_data.truth_lon,
                buffer_data.truth_lat,
                linewidth=2.0,
                label="Truth Track",
                zorder=2
            )

            plot_widget.ax.plot(
                buffer_data.gps_lon,
                buffer_data.gps_lat,
                linewidth=1.2,
                linestyle=":",
                label="GPS Track",
                zorder=2
            )

            plot_widget.ax.scatter(
                [buffer_data.truth_lon[-1]],
                [buffer_data.truth_lat[-1]],
                s=60,
                label="Truth Current",
                zorder=3
            )

            if latest_frame is not None and latest_frame.gps_fix_valid:
                plot_widget.ax.scatter(
                    [buffer_data.gps_lon[-1]],
                    [buffer_data.gps_lat[-1]],
                    s=45,
                    marker="x",
                    label="GPS Current",
                    zorder=3
                )

            if auto_follow:
                lon_min = min(min(buffer_data.truth_lon), min(buffer_data.gps_lon))
                lon_max = max(max(buffer_data.truth_lon), max(buffer_data.gps_lon))
                lat_min = min(min(buffer_data.truth_lat), min(buffer_data.gps_lat))
                lat_max = max(max(buffer_data.truth_lat), max(buffer_data.gps_lat))

                pad_lon = max((lon_max - lon_min) * 0.35, 0.05)
                pad_lat = max((lat_max - lat_min) * 0.35, 0.05)

                plot_widget.ax.set_xlim(lon_min - pad_lon, lon_max + pad_lon)
                plot_widget.ax.set_ylim(lat_min - pad_lat, lat_max + pad_lat)
        else:
            if auto_follow:
                plot_widget.ax.set_xlim(-53.5, -52.0)
                plot_widget.ax.set_ylim(4.5, 6.0)

        handles, _ = plot_widget.ax.get_legend_handles_labels()
        if handles:
            plot_widget.ax.legend(loc="upper left", fontsize=8)

        if not auto_follow:
            plot_widget.restore_axis_limits(limits)

        plot_widget.draw_idle_safe()