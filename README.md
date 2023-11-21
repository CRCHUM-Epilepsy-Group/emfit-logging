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

## Plugging the GPIO

![GPIO Pinout Diagram. We are interested in the pins in the blue box.](/.github/images/GPIO-Pinout-Diagram-Small.png)

The GPIO pins used by the connector are the ones shown in the picture above.
The connector uses a 1x8P Dupont connector group (black plastic rectangle), making it easier to plug it correctly in the GPIO.
You first need to locate the small arrow on one side of the Dupont connector, as illustrated (the white arrow is added to accentuate the arrow in the picture).

![Location of the small arrow on the connector. White arrow added for emphasis.](/.github/images/small-arrow.jpg)

Then, plug the connector with the small arrow being at the top left pin in the diagram (the one labeled "3V3 power"), goind down the GPIO headers.
The following pictures show a connector correctly plugged in:

| Connected View 1                                                | Connected View 2                                                |
| --------------------------------------------------------------- | --------------------------------------------------------------- |
| ![Connected View 1](/.github/images/connection/connected-1.jpg) | ![Connected View 2](/.github/images/connection/connected-2.jpg) |

### With a Case Cover

When installed in a patient's room, leaving the Raspberry Pi uncovered is not recommended.
The original Raspberry Pi 4 case does not have holes allowing access to the GPIO pins, so some 3D printed ones might be necessary.
An easy way to use the ones available with the CRCHUM Epilepsy Group is to pass the cable first, then close the case:

1. Pass the cable through the GPIO opening in the top cover.
![Pass the cable through the GPIO opening in the top cover.](/.github/images/connection/step-1.jpg)
2. Connect the GPIO connector to the Raspberry Pi.
![Connect the GPIO connector to the Raspberry Pi.](/.github/images/connection/step-2.jpg)
3. Close the case.
![Close the case.](/.github/images/connection/step-3.jpg)
4. Connect the other end of the connector to the X2 port on the Emfit control unit.
![Connect the other end of the connector to the X2 port on the Emfit control unit.](/.github/images/connection/step-4.jpg)

### Making Connectors
The CRCHUM Epilepsy Group should have around 10 cables already made for this specific purpose.
In case more are needed, here is the procedure to make some.

1. Get an Ethernet cable. The ones that were used here have the ["B" pinout](rj45b).
2. Cut one end of the cable. Ideal length from the remaining end to the cut section should be around 3 feet, to be able to connect easily between the Emfit control unit and the Raspberry Pi. As a tip, if using 6 feet cables, cutting it in half will allow to make two 3-feet connectors.
3. Expose the internal wires.

   ![Internal Wires of a RJ45 Connector](https://www.srgclub.org/images/CatCable.jpg)

4. Isolate the [wires 1 through 4](rj45b) (white-orange, solid-orange, white-green, and solid-blue). The other wires won't be needed for the connector as the Emfit control unit does not use them at all.
5. Use a wire stripper to strip 1-2 mm off the end of the insulation of each wires.
6. Use a crimping tool to attach a female Dupont 2.54 mm at the end of the 4 exposed wires.
7. To make it easier to connect to the correct GPIO pins, it is recommended to use a 1x8P plastic connector to group the Dupont pins together, leaving the first 4 positions of the connector empty (starting from the small arrow) and then placing the wires 1 through 4 in order in the remaining 4 positions, as illustrated:

  ![GPIO end of the connector](/.github/images/emfit-connector-Small.jpg)

[gpio]: https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio-and-the-40-pin-header
[rj45b]: https://www.showmecables.com/media/wysiwyg/RJ45-Pinout-T568B.jpg
