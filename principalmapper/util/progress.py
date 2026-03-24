"""Progress tracking UI for PMapper graph creation using ANSI escape codes (zero dependencies)."""

#  Copyright (c) NCC Group and Erik Steringer 2019. This file is part of Principal Mapper.
#
#      Principal Mapper is free software: you can redistribute it and/or modify
#      it under the terms of the GNU Affero General Public License as published by
#      the Free Software Foundation, either version 3 of the License, or
#      (at your option) any later version.
#
#      Principal Mapper is distributed in the hope that it will be useful,
#      but WITHOUT ANY WARRANTY; without even the implied warranty of
#      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#      GNU Affero General Public License for more details.
#
#      You should have received a copy of the GNU Affero General Public License
#      along with Principal Mapper.  If not, see <https://www.gnu.org/licenses/>.

import os
import sys
import time
import threading
from typing import List, Optional


# ANSI escape codes
_CLEAR_LINE = '\033[2K'
_MOVE_UP = '\033[A'
_HIDE_CURSOR = '\033[?25l'
_SHOW_CURSOR = '\033[?25h'
_BOLD = '\033[1m'
_DIM = '\033[2m'
_CYAN = '\033[36m'
_GREEN = '\033[32m'
_YELLOW = '\033[33m'
_WHITE = '\033[37m'
_RESET = '\033[0m'
_BG_DARK = '\033[48;5;236m'

# Block characters for progress bar
_BLOCK_FULL = '█'
_BLOCK_EMPTY = '░'


class ProgressTracker:
    """Thread-safe progress tracker for PMapper graph creation.

    Renders a boxed progress UI to the terminal using ANSI codes.
    Falls back to simple line output for non-TTY environments (piped output, CI, etc).
    """

    def __init__(self, title: str = 'PMapper Graph Creation', phases: Optional[List[str]] = None):
        self._title = title
        self._phases = phases or []
        self._total_phases = len(self._phases)
        self._current_phase = 0
        self._current_phase_name = ''
        self._current_step = ''
        self._sub_progress = 0.0  # 0.0 to 1.0 within current phase
        self._start_time = time.time()
        self._lock = threading.Lock()
        self._is_tty = hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()
        self._lines_drawn = 0
        self._completed_steps: List[str] = []

        if self._is_tty:
            sys.stderr.write(_HIDE_CURSOR)
            sys.stderr.flush()

    def set_phase(self, phase_name: str, step: str = ''):
        """Move to the next phase. Automatically increments the phase counter."""
        with self._lock:
            self._current_phase += 1
            self._current_phase_name = phase_name
            self._current_step = step
            self._sub_progress = 0.0
            self._render()

    def set_step(self, step: str, sub_progress: Optional[float] = None):
        """Update the current step indicator within the current phase."""
        with self._lock:
            self._current_step = step
            if sub_progress is not None:
                self._sub_progress = max(0.0, min(1.0, sub_progress))
            self._render()

    def set_sub_progress(self, progress: float):
        """Set the sub-progress within the current phase (0.0 to 1.0)."""
        with self._lock:
            self._sub_progress = max(0.0, min(1.0, progress))
            self._render()

    def complete_phase(self, message: str = ''):
        """Mark the current phase as complete."""
        with self._lock:
            self._sub_progress = 1.0
            if message:
                self._completed_steps.append(message)
            self._render()

    def finish(self, message: str = ''):
        """Finish progress tracking, show cursor, and print final message."""
        with self._lock:
            if self._is_tty:
                self._clear_rendered()
                sys.stderr.write(_SHOW_CURSOR)
                sys.stderr.flush()
            if message:
                sys.stderr.write(message + '\n')
                sys.stderr.flush()

    def _render(self):
        """Render the progress display. Must be called with lock held."""
        if self._is_tty:
            self._render_tty()
        else:
            self._render_simple()

    def _clear_rendered(self):
        """Clear previously rendered lines."""
        if self._lines_drawn > 0:
            for _ in range(self._lines_drawn):
                sys.stderr.write(_MOVE_UP + _CLEAR_LINE + '\r')
            self._lines_drawn = 0

    def _render_tty(self):
        """Render the full boxed progress UI for TTY terminals."""
        self._clear_rendered()

        elapsed = time.time() - self._start_time
        overall_progress = 0.0
        if self._total_phases > 0:
            completed = (self._current_phase - 1) / self._total_phases
            current_contribution = self._sub_progress / self._total_phases
            overall_progress = completed + current_contribution

        # Build the bar
        bar_width = 40
        filled = int(bar_width * overall_progress)
        bar = _BLOCK_FULL * filled + _BLOCK_EMPTY * (bar_width - filled)
        pct = int(overall_progress * 100)

        lines = []
        box_width = 62

        # Top border
        lines.append('  {}╔{}╗{}'.format(_CYAN, '═' * box_width, _RESET))

        # Title
        title_text = '  {}  '.format(self._title)
        lines.append('  {}║{}{}{:<{w}}║{}'.format(_CYAN, _BOLD, _WHITE, title_text, _RESET, w=box_width))

        # Separator
        lines.append('  {}╠{}╣{}'.format(_CYAN, '═' * box_width, _RESET))

        # Phase info
        phase_text = '  Phase {}/{}: {}'.format(self._current_phase, self._total_phases, self._current_phase_name)
        lines.append('  {}║{}{:<{w}}║{}'.format(_CYAN, _WHITE, phase_text, _RESET, w=box_width))

        # Progress bar with step
        step_display = '  [{}]'.format(self._current_step) if self._current_step else ''
        bar_line = '  {}{} {:>3}%{}{}'.format(_GREEN, bar, pct, _RESET + _DIM, step_display)
        # For alignment, we need to account for ANSI codes taking no visual width
        # Just pad the visible content to box_width
        visible_len = 2 + bar_width + 1 + 4 + len(step_display)
        pad_needed = max(0, box_width - visible_len)
        bar_line_padded = '  {} {:>3}%  {}{}'.format(bar, pct, step_display, ' ' * pad_needed)
        lines.append('  {}║{}{}{:<{w}}{}║{}'.format(
            _CYAN, _GREEN, '', bar_line_padded, _CYAN, _RESET, w=0))

        # Elapsed time
        elapsed_text = '  Elapsed: {:.1f}s'.format(elapsed)
        lines.append('  {}║{}{:<{w}}║{}'.format(_CYAN, _DIM + _WHITE, elapsed_text, _RESET + _CYAN, w=box_width))

        # Bottom border
        lines.append('  {}╚{}╝{}'.format(_CYAN, '═' * box_width, _RESET))

        output = '\n'.join(lines) + '\n'
        sys.stderr.write(output)
        sys.stderr.flush()
        self._lines_drawn = len(lines)

    def _render_simple(self):
        """Simple line-based rendering for non-TTY environments."""
        elapsed = time.time() - self._start_time
        step_info = ' [{}]'.format(self._current_step) if self._current_step else ''
        pct = int(self._sub_progress * 100)
        sys.stderr.write('[{:.1f}s] Phase {}/{}: {} {}%{}\n'.format(
            elapsed, self._current_phase, self._total_phases,
            self._current_phase_name, pct, step_info))
        sys.stderr.flush()
