import sys
import time
from io import StringIO

from rich import box
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from building import Building
from elevator import Direction
from passenger import Passenger
from simulation import Simulation


class Visualizer:
    def __init__(self, simulation, passengers):
        self.sim = simulation
        self.passengers = passengers
        self.log_lines = []
        self.console = Console()

    def _capture_tick(self):
        """Transition transient statuses, then run one sim tick capturing print output."""
        for p in self.passengers:
            if p.status == "boarding":
                p.status = "riding"
            elif p.status == "leaving":
                p.status = "arrived"

        old_stdout = sys.stdout
        sys.stdout = buf = StringIO()
        self.sim.tick()
        sys.stdout = old_stdout
        lines = [l for l in buf.getvalue().splitlines() if l.strip()]
        self.log_lines.extend(lines)
        self.log_lines = self.log_lines[-12:]

    def _passenger_status(self, passenger):
        STATUS_COLORS = {
            "waiting":  "yellow",
            "boarding": "bright_green",
            "riding":   "cyan",
            "leaving":  "bright_yellow",
            "arrived":  "green",
        }
        return (passenger.status.capitalize(), STATUS_COLORS.get(passenger.status, "white"))

    def _render(self):
        building = self.sim.building
        elevators = building.elevators

        # --- Building grid ---
        grid = Table(box=box.SIMPLE_HEAD, show_header=True, padding=(0, 1))
        grid.add_column("Floor", style="bold", width=7, justify="right")
        for elev in elevators:
            grid.add_column(f"Elev {elev.elevator_id}", width=14, justify="center")
        grid.add_column("Waiting", min_width=20)

        for floor in range(building.floors - 1, -1, -1):
            cells = []
            for elev in elevators:
                if elev.current_floor == floor:
                    arrow = {"UP": "▲", "DOWN": "▼", "IDLE": "■"}[elev.direction.name]
                    n_pax = len(elev.current_passengers)
                    cells.append(f"[bold green]{arrow} E{elev.elevator_id}[/bold green] ({n_pax})")
                elif floor in elev.destination_floor:
                    cells.append("[dim yellow]  ◦[/dim yellow]")
                else:
                    cells.append("")

            waiting = [
                p for p in self.passengers
                if self._passenger_status(p)[0] == "Waiting" and p.current_floor == floor
            ]
            waiting_str = "  ".join(
                f"[yellow]P{p.passenger_id}→{p.destination_floor}[/yellow]" for p in waiting
            )

            grid.add_row(f"{floor:2d}", *cells, waiting_str)

        # --- Passenger status table ---
        pax_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
        pax_table.add_column("ID",     width=4)
        pax_table.add_column("From",   width=6, justify="center")
        pax_table.add_column("To",     width=6, justify="center")
        pax_table.add_column("Status", width=10)

        for p in self.passengers:
            status, color = self._passenger_status(p)
            pax_table.add_row(
                f"P{p.passenger_id}",
                str(p.current_floor),
                str(p.destination_floor),
                f"[{color}]{status}[/{color}]",
            )

        # --- Event log ---
        log_text = "\n".join(self.log_lines[-10:]) or "[dim](no events yet)[/dim]"

        return Group(
            Panel(
                grid,
                title=f"[bold blue]{building.name}[/bold blue]  [dim]Tick {self.sim.tick_count}[/dim]",
                border_style="blue",
            ),
            Panel(pax_table, title="Passengers", border_style="cyan"),
            Panel(log_text,  title="Event Log",  border_style="dim"),
        )

    def _all_arrived(self):
        return all(p.status in ("arrived", "leaving") for p in self.passengers)

    def run(self, max_ticks=None):
        with Live(self._render(), refresh_per_second=4, console=self.console) as live:
            self.sim.running = True
            while self.sim.running:
                self._capture_tick()
                live.update(self._render())
                if self._all_arrived():
                    self.sim.running = False
                    break
                if max_ticks and self.sim.tick_count >= max_ticks:
                    self.sim.running = False
                    break
                time.sleep(self.sim.tick_rate)

        self.console.print(
            f"\n[bold green]Simulation complete — {self.sim.tick_count} ticks.[/bold green]"
        )


