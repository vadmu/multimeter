from visa_interface import VISAInterface
import logging 


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)6s - %(levelname)5s - %(message)s', level=logging.DEBUG
    )
    try:
        multimeter = VISAInterface(
            address='USB0::0x0957::0x0607::MY47001094::0::INSTR',
            logger_name="Keysight 34410A"
        )
        multimeter.talk("*IDN?")
    except ConnectionError:
        logging.error(
            "Something wrong with the connection. "
            "Please, check if the device is on, "
            "is set to remote control and the address is correct"
        )
