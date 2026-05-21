import logging
import pathlib
import shlex
import subprocess
import sys

logger = logging.getLogger("logger")


def start_in_terminal(cwd: pathlib.Path, args: list[str], title: str) -> bool:
    if sys.platform.startswith("linux"):
        python_cmd = shlex.join(args)
        command = f"{python_cmd}; exec bash"
        launch_options = [
            ["gnome-terminal", "--title", title, "--", "bash", "-lc", command],
            ["xterm", "-e", "bash", "-lc", command],
            ["x-terminal-emulator", "-e", "bash", "-lc", shlex.quote(command)],
            ["konsole", "-e", "bash", "-lc", command],
        ]
        for args in launch_options:
            try:
                proc = subprocess.Popen(
                    args,
                    cwd=cwd,
                    start_new_session=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            except (FileNotFoundError, OSError):
                continue
            else:
                logger.info(f"Started: {' '.join(args)}")
                if False:
                    # Just for debugging
                    import time

                    time.sleep(2.0)
                    stdout, stderr = proc.communicate(timeout=2.0)
                    rc = proc.wait(timeout=2.0)
                    logger.info(f"proc.stdout={stdout}")
                    logger.info(f"proc.stderr={stderr}")
                    logger.info(f"proc.rc={rc}")
                return True
        logger.error(f"Failed to start: {args}")

    if sys.platform == "win32":
        subprocess.Popen(
            args=args,
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=cwd,
        )

    return False
