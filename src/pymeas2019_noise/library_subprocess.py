import logging
import pathlib
import shlex
import subprocess
import sys

logger = logging.getLogger("logger")


def start_in_terminal(cwd: pathlib.Path, args: list[str]) -> bool:
    if sys.platform.startswith("linux"):
        python_cmd = shlex.join(args)
        command = f"{python_cmd}; exec bash"
        quoted_command = shlex.quote(command)
        launch_options = [
            ["x-terminal-emulator", "-e", "bash", "-lc", quoted_command],
            ["gnome-terminal", "--", "bash", "-lc", quoted_command],
            ["konsole", "-e", "bash", "-lc", quoted_command],
            ["xterm", "-e", "bash", "-lc", quoted_command],
        ]
        for args in launch_options:
            try:
                subprocess.Popen(
                    args,
                    cwd=cwd,
                    start_new_session=True,
                )
            except (FileNotFoundError, OSError):
                continue
            else:
                logger.info(f"Started: {args}")
                return True
        logger.error(f"Failed to start: {args}")

    if sys.platform == "win32":
        subprocess.Popen(
            args=args,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=cwd,
        )

    return False
