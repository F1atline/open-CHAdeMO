import logging

def source():
    def __init__(self, voltage, current):
        self.voltage = voltage
        self.current = current

    def check_status(self):
        if self.voltage == 0:
            return 0


def consumer():
    def __init__(self, voltage, current):
        self.voltage = voltage
        self.current = current

def main():
    charger = source(0, 0)
    charger.check_status()
    logging.info("Started!")

if __name__ == '__main__':
    main()