import socket
from datetime import datetime

class PackagePrinter:
    """Handles printing of package receipts using ESC/POS commands"""

    def __init__(self, ip="192.168.10.175", port=9100):
        self.PRINTER_IP = ip
        self.PRINTER_PORT = port

        # ESC/POS commands
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

    def print_package_receipt(self, package_data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as printer:
                printer.connect((self.PRINTER_IP, self.PRINTER_PORT))

                # -- Header Section --
                printer.sendall(self.CENTER_ALIGN + self.BOLD_ON)
                printer.sendall(b"PARKLANDS SPORTS CLUB\n")
                printer.sendall(self.BOLD_OFF)
                printer.sendall(b"PO BOX 123-456, NAIROBI\n")
                printer.sendall(b"Tel: 0712 345 6789\n")
                printer.sendall(b"Web: www.parklandssportsclub.org\n")
                printer.sendall(b"\n")

                # Title
                printer.sendall(self.BOLD_ON + b"PACKAGE RECEIPT\n")
                printer.sendall(self.BOLD_OFF + self.LINE_FEED)

                # Package Code - Large
                printer.sendall(self.CENTER_ALIGN + self.BOLD_ON + self.QUAD_SIZE_ON)
                printer.sendall(f"{package_data['code']}\n".encode('utf-8'))
                printer.sendall(self.NORMAL_SIZE + self.BOLD_OFF + self.LINE_FEED)

                # -- Package Details --
                printer.sendall(self.LEFT_ALIGN + self.BOLD_ON)
                printer.sendall(b"Package Details\n")
                printer.sendall(self.BOLD_OFF + b"-----------------------------\n")
                printer.sendall(self.BOLD_ON + b"Type: ")
                printer.sendall(self.BOLD_OFF + package_data['type'].encode('utf-8') + self.LINE_FEED)

                printer.sendall(self.BOLD_ON + b"Description: ")
                printer.sendall(self.BOLD_OFF + package_data['description'].encode('utf-8') + self.LINE_FEED)

                if 'shelf' in package_data and package_data['shelf']:
                    printer.sendall(self.BOLD_ON + b"Shelf: ")
                    printer.sendall(self.BOLD_OFF + package_data['shelf'].encode('utf-8') + self.LINE_FEED)

                # -- Recipient Info --
                printer.sendall(b"\n" + self.BOLD_ON + b"Recipient Information\n")
                printer.sendall(self.BOLD_OFF + b"-----------------------------\n")
                printer.sendall(self.BOLD_ON + b"Name: ")
                printer.sendall(self.BOLD_OFF + package_data['recipient_name'].encode('utf-8') + self.LINE_FEED)

                printer.sendall(self.BOLD_ON + b"Phone: ")
                printer.sendall(self.BOLD_OFF + package_data['recipient_phone'].encode('utf-8') + self.LINE_FEED)

                # -- Dropper Info --
                printer.sendall(b"\n" + self.BOLD_ON + b"Dropped By\n")
                printer.sendall(self.BOLD_OFF + b"-----------------------------\n")
                printer.sendall(self.BOLD_ON + b"Name: ")
                printer.sendall(self.BOLD_OFF + package_data['dropped_by'].encode('utf-8') + self.LINE_FEED)

                printer.sendall(self.BOLD_ON + b"Phone: ")
                printer.sendall(self.BOLD_OFF + package_data['dropper_phone'].encode('utf-8') + self.LINE_FEED)

                # -- Date & Time --
                printer.sendall(b"\n" + self.BOLD_ON + b"Date: ")
                printer.sendall(self.BOLD_OFF + datetime.now().strftime("%Y-%m-%d %H:%M").encode('utf-8') + self.LINE_FEED)

                # -- Created By --
                if 'created_by' in package_data:
                    printer.sendall(self.BOLD_ON + b"Created By: ")
                    printer.sendall(self.BOLD_OFF + package_data['created_by'].encode('utf-8') + self.LINE_FEED)

                # -- QR Code --
                qr_data = package_data['code']
                printer.sendall(b"\n" + self.CENTER_ALIGN)

                store_len = len(qr_data) + 3
                pL = store_len % 256
                pH = store_len // 256
                printer.sendall(self.GS + b'(k' + bytes([pL, pH]) + b'\x31\x50\x30' + qr_data.encode('utf-8'))
                printer.sendall(self.GS + b'(k\x03\x00\x31\x41\x32')  # Model 2
                printer.sendall(self.GS + b'(k\x03\x00\x31\x43\x06')  # Size
                printer.sendall(self.GS + b'(k\x03\x00\x31\x45\x30')  # Error correction
                printer.sendall(self.GS + b'(k\x03\x00\x31\x51\x30')  # Print

                # -- Footer --
                printer.sendall(b"\n" * 2 + self.CENTER_ALIGN + self.BOLD_ON)
                printer.sendall(b"Thank you for using PSC Package Service\n")
                printer.sendall(b"Handled by PSC ICT Department\n")
                printer.sendall(self.BOLD_OFF + b"\n")

                printer.sendall(b"\n" * 3)
                printer.sendall(self.CUT)

            return True
        except Exception as e:
            print(f"Printing failed: {str(e)}")
            return False
