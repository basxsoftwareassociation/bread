import shutil
import subprocess  # nosec


def systemfonts():
    result = []
    for fontentry in (
        subprocess.run(  # nosec
            [shutil.which("fc-list") or "false"], shell=False, capture_output=True
        )
        .stdout.decode()
        .splitlines()
    ):
        result.extend(
            [i.strip() for i in fontentry.split(":", 1)[1].split(":", 1)[0].split(",")]
        )
    return result
