import pyvisa
import logging


TIMEOUT_IN_SECONDS = 5


class VISAInterface:
    def __init__(self, address, logger_name):
        visa_logger = logging.getLogger('pyvisa')
        visa_logger.setLevel(logging.INFO)  # pyvisa generates too many debug messages
        self.logger = logging.getLogger(logger_name)
        self.rm = pyvisa.ResourceManager()
        self.address = address
        try:
            self.inst = self.rm.open_resource(address)
            self.inst.timeout = TIMEOUT_IN_SECONDS * 1000
            self.logger.info(f"VISA interface {self.address} connected.")
        except pyvisa.errors.VisaIOError:
            self.inst = None
            self.logger.error(f"Could not connect to VISA interface {self.address}.")
            raise ConnectionError(f"Could not connect to VISA interface {self.address}.")

    def write(self, cmd):
        self.logger.debug(cmd)
        self.inst.write(cmd)

    def read(self):
        reply = self.inst.read_raw()
        self.logger.debug(reply)
        return reply

    def talk(self, cmd):
        self.logger.debug(cmd)
        reply = self.inst.query(cmd)
        self.logger.debug(reply.strip())
        return reply.strip()

    def close(self):
        if self.inst:
            self.inst.close()
            self.logger.info(f"VISA interface {self.address} disconnected.")
