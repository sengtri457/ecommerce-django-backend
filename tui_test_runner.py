#!/usr/bin/env python
"""
Interactive TUI Test Runner for Clothes™ & CTRL E-Commerce Backend.
Executes test suites and renders a real-time, rich terminal dashboard.
"""

import os
import sys
import time
import unittest
from decimal import Decimal

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test.runner import DiscoverRunner
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout

console = Console()

class TUIResult(unittest.TestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_records = []
        self._start_time = 0.0

    def startTest(self, test):
        super().startTest(test)
        self._start_time = time.perf_counter()

    def addSuccess(self, test):
        super().addSuccess(test)
        elapsed = (time.perf_counter() - self._start_time) * 1000
        module = test.__class__.__module__.replace('tests.', '')
        name = test._testMethodName
        doc = test._testMethodDoc or ""
        self.test_records.append({
            'module': module,
            'name': name,
            'doc': doc.strip(),
            'time': elapsed,
            'status': 'PASSED',
            'error': None
        })

    def addFailure(self, test, err):
        super().addFailure(test, err)
        elapsed = (time.perf_counter() - self._start_time) * 1000
        module = test.__class__.__module__.replace('tests.', '')
        name = test._testMethodName
        self.test_records.append({
            'module': module,
            'name': name,
            'doc': (test._testMethodDoc or "").strip(),
            'time': elapsed,
            'status': 'FAILED',
            'error': self._exc_info_to_string(err, test)
        })

    def addError(self, test, err):
        super().addError(test, err)
        elapsed = (time.perf_counter() - self._start_time) * 1000
        module = test.__class__.__module__.replace('tests.', '')
        name = test._testMethodName
        self.test_records.append({
            'module': module,
            'name': name,
            'doc': (test._testMethodDoc or "").strip(),
            'time': elapsed,
            'status': 'ERROR',
            'error': self._exc_info_to_string(err, test)
        })

class TUITestRunner(DiscoverRunner):
    def get_resultclass(self):
        return TUIResult

def run_tui():
    header_text = Text()
    header_text.append(" Clothes™ / CTRL — Backend Test Dashboard ", style="bold white on black")
    header_text.append(" [3NF Relational & Concurrency Engine]", style="dim italic")
    console.print(Panel(header_text, border_style="cyan"))

    runner = TUITestRunner(verbosity=0, interactive=False)
    runner.setup_test_environment()
    old_config = runner.setup_databases()

    suite = runner.build_suite(test_labels=['tests'])
    result = TUIResult()

    start_total = time.perf_counter()
    with console.status("[bold cyan]Running automated test suites in TUI...", spinner="dots"):
        suite.run(result)
    total_time = time.perf_counter() - start_total

    runner.teardown_databases(old_config)
    runner.teardown_test_environment()

    # Build Results Table
    table = Table(
        title="Automated Test Suite Execution Details",
        title_style="bold cyan",
        border_style="bright_black",
        header_style="bold white",
        show_lines=True,
    )
    table.add_column("#", justify="center", style="dim", width=4)
    table.add_column("Domain / Suite", style="magenta", width=28)
    table.add_column("Test Case Method & Intent", style="white", min_width=38)
    table.add_column("Latency", justify="right", style="cyan", width=12)
    table.add_column("Status", justify="center", width=12)

    for idx, rec in enumerate(result.test_records, start=1):
        if rec['status'] == 'PASSED':
            status_badge = "[bold green]✓ PASSED[/bold green]"
        elif rec['status'] == 'FAILED':
            status_badge = "[bold red]✗ FAILED[/bold red]"
        else:
            status_badge = "[bold yellow]! ERROR[/bold yellow]"

        desc = f"[bold]{rec['name']}[/bold]"
        if rec['doc']:
            desc += f"\n[dim]{rec['doc']}[/dim]"

        table.add_row(
            str(idx),
            rec['module'],
            desc,
            f"{rec['time']:.1f} ms",
            status_badge
        )

    console.print(table)

    # Print Summary Card
    total_count = len(result.test_records)
    passed_count = sum(1 for r in result.test_records if r['status'] == 'PASSED')
    failed_count = sum(1 for r in result.test_records if r['status'] in ('FAILED', 'ERROR'))

    summary_color = "green" if failed_count == 0 else "red"
    summary_text = (
        f"[bold {summary_color}]Summary:[/bold {summary_color}] "
        f"[bold]{total_count}[/bold] total tests executed in [bold cyan]{total_time:.2f}s[/bold cyan] "
        f"• [bold green]{passed_count} passed[/bold green] "
        f"• [bold red]{failed_count} failed[/bold red]\n"
        f"[dim]Environment: Python {sys.version.split()[0]} | Django 6.1.1 | Relational SQLite3 Engine[/dim]"
    )
    console.print(Panel(summary_text, border_style=summary_color, title="[bold]Test Suite Result[/bold]"))

    # Failures Detail if any
    for rec in result.test_records:
        if rec['error']:
            console.print(Panel(rec['error'], title=f"[bold red]Failure in {rec['name']}[/bold red]", border_style="red"))

    if failed_count > 0:
        sys.exit(1)

if __name__ == '__main__':
    run_tui()
