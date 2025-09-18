import logging
import platform
import signal
import socket
import tomllib
from datetime import datetime
from pathlib import Path
from time import sleep
from zoneinfo import ZoneInfo

import discord
import gpiozero
import requests
from redcap.project import Project
from typing_extensions import deprecated

PROJ_ROOT = Path(__file__).parent.resolve()
logging.basicConfig(
    filename=PROJ_ROOT / "emfit-logging.log",
    format="[%(asctime)s] %(levelname)s: %(message)s",
    level=logging.DEBUG,
)
LOGGER = logging.getLogger("emfit-logging")
with (PROJ_ROOT / "config.toml").open("rb") as f:
    CONFIG = tomllib.load(f)
ALARMS_LOG_FILE = (
    PROJ_ROOT
    / f"alarms-{socket.gethostname()}_record-{CONFIG['redcap']['REDCAP_RECORD_ID']}.log"
)


def dt_now() -> datetime:
    """Get the current time at the configurated timezone.

    Returns
    -------
    datetime
        The current timezone-aware time.

    """
    return datetime.now(tz=ZoneInfo(CONFIG["timezone"]))


def setup_pin_factory() -> None:
    match platform.system():
        case "Linux":
            from gpiozero.pins.lgpio import LGPIOFactory

            LOGGER.debug("Setting pin factory to LGPIOFactory (Linux)")
            gpiozero.Device.pin_factory = LGPIOFactory()

        case "Windows":
            from gpiozero.pins.mock import MockFactory

            LOGGER.debug("Setting pin factory to MockFactory (Windows)")
            gpiozero.Device.pin_factory = MockFactory()


def test_alarm(device: gpiozero.DigitalInputDevice) -> None:
    """Simulate an alarm from the AUX port of the Emfit device.

    This is only used when testing the script from a Windows machine,
    where there are no GPIO pins.
    """
    from gpiozero.pins.mock import MockPin

    time_active = 1.5
    LOGGER.debug(f"Simulating pin activation for {time_active:.1f} s")

    assert isinstance(device.pin, MockPin)  # noqa: S101

    sleep(1)
    device.pin.drive_low()
    LOGGER.debug(f"Pin active, sleeping for {time_active:.1f} s")
    sleep(time_active)
    device.pin.drive_high()
    LOGGER.debug("Pin deactivated")


def save_alarm_to_file(alarm_time: datetime) -> None:
    """Append the alarm datetime to the ALARMS_LOG_FILE, in ISO 8601 format."""
    with ALARMS_LOG_FILE.open("a+") as f:
        f.write(f"{alarm_time.isoformat(sep=' ')}\n")


def send_alarms_to_redcap() -> None:
    """Send the ALARMS_LOG_FILE to the REDCap instance.

    Configuration for the REDCap API project and field are under config.toml.
    """
    LOGGER.info(f"Sending {ALARMS_LOG_FILE.name} to REDCap")
    redcap_project = Project(
        CONFIG["redcap"]["REDCAP_API_URL"], CONFIG["redcap"]["REDCAP_API_TOKEN"]
    )
    with ALARMS_LOG_FILE.open() as f:
        # Import file == upload to REDCap
        redcap_project.import_file(
            record=CONFIG["redcap"]["REDCAP_RECORD_ID"],
            field=CONFIG["redcap"]["REDCAP_FILE_FIELD"],
            file_name=ALARMS_LOG_FILE.name,
            file_object=f,
            event=(
                CONFIG["redcap"]["REDCAP_EVENT_NAME"]
                if redcap_project.is_longitudinal
                else None
            ),
        )


@deprecated("Use send_message_to_discord instead.")
def send_message_to_slack(alarm_time: datetime) -> None:
    """Send the alarm to Slack through a webhook."""
    url: str = CONFIG["slack"]["WEBHOOK_URL"]
    formatted_time = (
        f"<!date^{int(alarm_time.timestamp())}^{{date_num}}, {{time}}|{alarm_time}>"
    )
    LOGGER.debug(f"{formatted_time=}")
    content = f"`{socket.gethostname()}` detected a seizure at {formatted_time}."

    LOGGER.info(f"To Slack: {content}")
    json_data = {"text": content}
    resp = requests.post(url, json=json_data, timeout=10)
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        LOGGER.exception(
            f"There was a {e.__class__.__name__} sending a message to Slack.",
        )


def send_message_to_discord(alarm_time: datetime) -> None:
    """Send the alarm to Discord through a webhook."""
    precise_time = discord.utils.format_dt(alarm_time, style="F")
    relative_time = discord.utils.format_dt(alarm_time, style="R")
    LOGGER.debug(f"{precise_time=}")
    description = (
        f"`{socket.gethostname()}` detected a seizure on "
        f"{precise_time} ({relative_time})."
    )
    LOGGER.info(f"To Discord: {description}")

    embed = discord.Embed(
        title="EMFIT Alarm Detected",
        description=description,
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow(),
    )

    webhook = discord.SyncWebhook.from_url(CONFIG["discord"]["WEBHOOK_URL"])
    try:
        webhook.send(embed=embed)

    except (discord.Forbidden, discord.NotFound, discord.HTTPException) as e:
        LOGGER.exception(
            f"Unable to send the message to Discord webhook ({e.__class__.__name__})"
        )


def alarm_detected() -> None:
    """Actions when the alarm starts.

    Currently, we:
        - Get the datetime
        - Save the datetime to the ALARMS_LOG_FILE
        - Try to send (upload) the file to REDCap
    """
    alarm_time = dt_now()
    LOGGER.debug(f"Alarm detected at {alarm_time}")
    save_alarm_to_file(alarm_time)
    try:
        send_alarms_to_redcap()
    except requests.exceptions.RequestException as e:
        LOGGER.exception(
            f"There was a {e.__class__.__name__} sending the file to REDCap.",
        )

    if CONFIG.get("discord"):
        send_message_to_discord(alarm_time)


def alarm_stopped() -> None:
    """Actions when the alarm stops."""
    LOGGER.debug(f"Alarm stopped at {dt_now()}")


def wait_for_alarms() -> None:
    """Set the actions to do when an alarm is detected."""
    LOGGER.info("Waiting for alarms...")

    device = gpiozero.DigitalInputDevice(CONFIG["emfit"]["AUX_2_PIN"], pull_up=True)
    device.when_activated = alarm_detected

    match platform.system():
        case "Linux":
            # This method only exists on Linux, so we ignore the warning on Windows
            signal.pause()  # type: ignore[]

        case "Windows":
            test_alarm(device)


def main() -> None:
    setup_pin_factory()
    LOGGER.info(f"Alarms log file saved to {ALARMS_LOG_FILE}")
    wait_for_alarms()


if __name__ == "__main__":
    main()
