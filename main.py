from datetime import datetime
import logging
from pathlib import Path
import platform
import signal
import socket
import sys
from time import sleep
import tomllib

import gpiozero
import requests

from redcap.methods.files import Files


PROJ_ROOT = Path(__file__).parent.resolve()
logging.basicConfig(
    filename=PROJ_ROOT / "emfit-logging.log",
    format="%(levelname)s: %(message)s",
    level=logging.DEBUG,
)
ALARMS_LOG_FILE = PROJ_ROOT / f"alarms-{socket.gethostname()}.log"
with open(PROJ_ROOT / "config.toml", "rb") as f:
    CONFIG = tomllib.load(f)


def setup_pin_factory() -> None:
    match platform.system():
        case "Linux":
            from gpiozero.pins.native import NativeFactory

            logging.debug("Setting pin factory to NativeFactory (Linux)")
            gpiozero.Device.pin_factory = NativeFactory()

        case "Windows":
            from gpiozero.pins.mock import MockFactory

            logging.debug("Setting pin factory to MockFactory (Windows)")
            gpiozero.Device.pin_factory = MockFactory()


def test_alarm(device: gpiozero.DigitalInputDevice) -> None:
    """Simulate an alarm from the AUX port of the Emfit device.
    This is only used when testing the script from a Windows machine,
    where there are no GPIO pins.
    """
    from gpiozero.pins.mock import MockPin

    time_active = 1.5
    logging.debug(f"Simulating pin activation for {time_active:.1f} s")

    assert isinstance(device.pin, MockPin)

    sleep(1)
    device.pin.drive_low()
    logging.debug(f"Pin active, sleeping for {time_active:.1f} s")
    sleep(time_active)
    device.pin.drive_high()
    logging.debug("Pin deactivated")


def save_alarm_to_file(alarm_time: datetime) -> None:
    """Append the alarm datetime to the ALARMS_LOG_FILE, in ISO 8601 format."""

    with open(ALARMS_LOG_FILE, "a+") as f:
        f.write(f"{alarm_time.isoformat(sep=' ')}\n")


def send_alarms_to_redcap() -> None:
    """Send the ALARMS_LOG_FILE to the REDCap instance, under the configured
    field in the dedicated project.

    Configuration for the REDCap API and project are under config.toml.
    """

    logging.info(f"Sending {ALARMS_LOG_FILE.name} to REDCap")
    redcap_files = Files(
        CONFIG["redcap"]["REDCAP_API_URL"], CONFIG["redcap"]["REDCAP_API_TOKEN"]
    )
    with open(ALARMS_LOG_FILE) as f:
        # Import file == upload to REDCap
        redcap_files.import_file(
            record=CONFIG["redcap"]["REDCAP_RECORD_ID"],
            field=CONFIG["redcap"]["REDCAP_FILE_FIELD"],
            file_name=ALARMS_LOG_FILE.name,
            file_object=f,
            event=CONFIG["redcap"]["REDCAP_EVENT_NAME"],
        )


def alarm_detected() -> None:
    """Actions when the alarm starts.
    Currently, we:
        - Get the datetime
        - Save the datetime to the ALARMS_LOG_FILE
        - Try to send (upload) the file to REDCap
    """

    alarm_time = datetime.now()
    logging.debug(f"Alarm detected at {alarm_time}")
    save_alarm_to_file(alarm_time)
    try:
        send_alarms_to_redcap()
    except requests.exceptions.RequestException as e:
        logging.exception(
            f"There was a {e.__class__.__name__} sending the file to REDCap.",
            exc_info=sys.exc_info(),
        )


def alarm_stopped() -> None:
    """Actions when the alarm stops."""

    logging.debug(f"Alarm stopped at {datetime.now()}")


def wait_for_alarms() -> None:
    """Main function to setup the actions to do when an alarm is detected."""

    logging.info("Waiting for alarms...")

    device = gpiozero.DigitalInputDevice(CONFIG["emfit"]["AUX_2_PIN"], pull_up=True)
    device.when_activated = alarm_detected

    match platform.system():
        case "Linux":
            # This method only exists on Linux, so we ignore the warning on Windows
            signal.pause()  # type: ignore

        case "Windows":
            test_alarm(device)


def main() -> None:
    setup_pin_factory()
    logging.info(f"Alarms log file saved to {ALARMS_LOG_FILE}")
    wait_for_alarms()


if __name__ == "__main__":
    main()
