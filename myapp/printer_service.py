import socket
from datetime import datetime

class PackagePrinter:
    def __init__(self, ip="192.168.110.175", port=9100):
        self.PRINTER_IP = ip
        self.PRINTER_PORT = port

        self.ESC = b'\x1b'
        self.GS = b'\x1d'
        self.BOLD_ON = self.ESC + b'\x45\x01'
        self.BOLD_OFF = self.ESC + b'\x45\x00'
        self.QUAD_SIZE_ON = self.GS + b'\x21\x33'
        self.NORMAL_SIZE = self.GS + b'\x21\x00'
        self.CENTER_ALIGN = self.ESC + b'\x61\x01'
        self.LEFT_ALIGN = self.ESC + b'\x61\x00'
        self.LINE_FEED = b'\n'
        self.CUT = self.GS + b'V\x00'

    def _send_header(self, printer):
        printer.sendall(self.CENTER_ALIGN + self.BOLD_ON)
        printer.sendall(b"PARKLANDS SPORTS CLUB\n")
        printer.sendall(self.BOLD_OFF)
        printer.sendall(b"PO BOX 123-456, NAIROBI\n")
        printer.sendall(b"Tel: 0712 345 6789\n")
        printer.sendall(b"www.parklandssportsclub.org\n\n")

    def _send_footer(self, printer):
        printer.sendall(b"\n" * 2 + self.CENTER_ALIGN + self.BOLD_ON)
        printer.sendall(b"Thank you for using PSC Package Service\n")
        printer.sendall(b"Handled by PSC Security\n")
        printer.sendall(b"Designed by JOHN ODERO\n")
        printer.sendall(self.BOLD_OFF + b"\n")
        printer.sendall(b"\n" * 3)
        printer.sendall(self.CUT)

    def print_label_receipt(self, package_data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as printer:
                printer.connect((self.PRINTER_IP, self.PRINTER_PORT))

                self._send_header(printer)

                printer.sendall(self.BOLD_ON + b"PACKAGE RECEIPT\n")
                printer.sendall(self.BOLD_OFF + self.LINE_FEED)

                printer.sendall(self.CENTER_ALIGN + self.BOLD_ON + self.QUAD_SIZE_ON)
                printer.sendall(f"{package_data['code']}\n".encode('utf-8'))
                printer.sendall(self.NORMAL_SIZE + self.BOLD_OFF + self.LINE_FEED)

                printer.sendall(self.LEFT_ALIGN + self.BOLD_ON + b"Details\n")
                printer.sendall(self.BOLD_OFF + b"-----------------------------\n")
                printer.sendall(self.BOLD_ON + b"Type: " + self.BOLD_OFF + package_data['type'].encode() + self.LINE_FEED)
                printer.sendall(self.BOLD_ON + b"Desc: " + self.BOLD_OFF + package_data['description'].encode() + self.LINE_FEED)
                if package_data.get('shelf'):
                    printer.sendall(self.BOLD_ON + b"Shelf: " + self.BOLD_OFF + package_data['shelf'].encode() + self.LINE_FEED)

                printer.sendall(self.BOLD_ON + b"Recipient: " + self.BOLD_OFF + package_data['recipient_name'].encode() + b" (" + package_data['recipient_phone'].encode() + b")" + self.LINE_FEED)

                printer.sendall(self.BOLD_ON + b"Dropper: " + self.BOLD_OFF + package_data['dropped_by'].encode() + b" (" + package_data['dropper_phone'].encode() + b")" + self.LINE_FEED)

                printer.sendall(self.BOLD_ON + b"Date: " + self.BOLD_OFF + datetime.now().strftime("%Y-%m-%d %H:%M").encode() + self.LINE_FEED)
                if 'created_by' in package_data:
                    printer.sendall(self.BOLD_ON + b"By: " + self.BOLD_OFF + package_data['created_by'].encode() + self.LINE_FEED)

                self._send_footer(printer)
            return True
        except Exception as e:
            print(f"Label print failed: {e}")
            return False

    def print_dropper_receipt(self, package_data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as printer:
                printer.connect((self.PRINTER_IP, self.PRINTER_PORT))

                self._send_header(printer)
                printer.sendall(self.BOLD_ON + b"OFFICIAL DROP RECEIPT\n" + self.BOLD_OFF)
                printer.sendall(self.CENTER_ALIGN + self.BOLD_ON + self.QUAD_SIZE_ON)
                printer.sendall(f"{package_data['code']}\n".encode())
                printer.sendall(self.NORMAL_SIZE + self.BOLD_OFF + self.LINE_FEED)

                printer.sendall(self.LEFT_ALIGN + self.BOLD_ON + b"Confirmation\n")
                printer.sendall(self.BOLD_OFF + b"-----------------------------\n")
                printer.sendall(b"This acknowledges receipt of a package\n")
                printer.sendall(b"delivered by:\n\n")
                printer.sendall(self.BOLD_ON + b"Name: " + self.BOLD_OFF + package_data['dropped_by'].encode() + self.LINE_FEED)
                printer.sendall(self.BOLD_ON + b"Phone: " + self.BOLD_OFF + package_data['dropper_phone'].encode() + self.LINE_FEED)
                printer.sendall(self.BOLD_ON + b"Date: " + self.BOLD_OFF + datetime.now().strftime("%Y-%m-%d %H:%M").encode() + self.LINE_FEED)

                printer.sendall(b"\nKeep this receipt for your records.\n")

                self._send_footer(printer)
            return True
        except Exception as e:
            print(f"Dropper print failed: {e}")
            return False
