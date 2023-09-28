# emfit-logging
Python script for Raspberry Pi to detect and log alarms triggered by the Emfit Movement Monitor to REDCap.

## Configuration
The configuration for this project needs a ``config.toml`` file to exist at the root of the project. You can use the ``config-example.toml`` file as a base to create your own configuration.

The configuration is in two parts:

- ``emfit``: Contains the [GPIO pin numbers](gpio) of the Raspberry Pi to connect the AUX cable (from the X2 port) from the Emfit control unit. The default configuration uses 4 consecutive pins on the Raspberry Pi for easier access.
- ``redcap``: Contains the REDCap configuration;
  - ``REDCAP_API_TOKEN``: The API token generated from the project page. This is very important to keep it secret!
  - ``REDCAP_API_URL``: The URL to the REDCap API. Usually, is it the web domain with ``/api/`` at the end.
  - ``REDCAP_FILE_FIELD``: The variable name of the field used to upload the file to. This needs to be a field in an instrument/form set to accept a file upload.
  - ``REDCAP_RECORD_ID``: The Record ID specific to the patient, in REDCap. This is probably the only configuration setting that will need to be modified regularly as new patients are admitted.

[gpio]: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header
