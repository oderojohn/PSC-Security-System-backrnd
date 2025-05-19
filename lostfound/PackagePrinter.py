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

    def print_found_receipt(self, found_item):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as printer:
                printer.connect((self.PRINTER_IP, self.PRINTER_PORT))

                printer.sendall(self.CENTER_ALIGN + self.BOLD_ON)
                printer.sendall(b"PARKLANDS SPORTS CLUB\n")
                printer.sendall(self.BOLD_OFF)
                printer.sendall(b"PO BOX 123-456, NAIROBI\n")
                printer.sendall(b"Tel: 0712 345 6789\n")
                printer.sendall(b"Web: www.parklandssportsclub.org\n")
                printer.sendall(b"\n")

                printer.sendall(self.BOLD_ON + b"FOUND ITEM RECEIPT\n")
                printer.sendall(self.BOLD_OFF + self.LINE_FEED)

                printer.sendall(self.CENTER_ALIGN + self.BOLD_ON + self.QUAD_SIZE_ON)
                printer.sendall(f"{found_item.id}\n".encode('utf-8'))
                printer.sendall(self.NORMAL_SIZE + self.BOLD_OFF + self.LINE_FEED)

                printer.sendall(self.LEFT_ALIGN + self.BOLD_ON)
                printer.sendall(b"Item Details\n")
                printer.sendall(self.BOLD_OFF + b"-----------------------------\n")
                printer.sendall(self.BOLD_ON + b"Type: ")
                printer.sendall(self.BOLD_OFF + str(found_item.type).encode('utf-8') + self.LINE_FEED)

                printer.sendall(self.BOLD_ON + b"Description: ")
                printer.sendall(self.BOLD_OFF + str(found_item.description).encode('utf-8') + self.LINE_FEED)

                printer.sendall(self.BOLD_ON + b"Place Found: ")
                printer.sendall(self.BOLD_OFF + str(found_item.place_found).encode('utf-8') + self.LINE_FEED)

                printer.sendall(b"\n" + self.BOLD_ON + b"Finder Information\n")
                printer.sendall(self.BOLD_OFF + b"-----------------------------\n")
                printer.sendall(self.BOLD_ON + b"Name: ")
                printer.sendall(self.BOLD_OFF + str(found_item.finder_name).encode('utf-8') + self.LINE_FEED)

                printer.sendall(self.BOLD_ON + b"Phone: ")
                printer.sendall(self.BOLD_OFF + str(found_item.finder_phone).encode('utf-8') + self.LINE_FEED)

                printer.sendall(b"\n" + self.BOLD_ON + b"Date Reported: ")
                printer.sendall(self.BOLD_OFF + found_item.date_reported.strftime("%Y-%m-%d %H:%M").encode('utf-8') + self.LINE_FEED)

                printer.sendall(self.BOLD_ON + b"Status: ")
                printer.sendall(self.BOLD_OFF + str(found_item.status).encode('utf-8') + self.LINE_FEED)

                qr_data = str(found_item.id)
                printer.sendall(b"\n" + self.CENTER_ALIGN)

                store_len = len(qr_data) + 3
                pL = store_len % 256
                pH = store_len // 256
                printer.sendall(self.GS + b'(k' + bytes([pL, pH]) + b'\x31\x50\x30' + qr_data.encode('utf-8'))
                printer.sendall(self.GS + b'(k\x03\x00\x31\x41\x32')
                printer.sendall(self.GS + b'(k\x03\x00\x31\x43\x06')
                printer.sendall(self.GS + b'(k\x03\x00\x31\x45\x30')
                printer.sendall(self.GS + b'(k\x03\x00\x31\x51\x30')

                printer.sendall(b"\n" * 2 + self.CENTER_ALIGN + self.BOLD_ON)
                printer.sendall(b"Thank you for using PSC Lost+Found\n")
                printer.sendall(b"Handled by PSC ICT Department\n")
                printer.sendall(self.BOLD_OFF + b"\n")

                printer.sendall(b"\n" * 3)
                printer.sendall(self.CUT)

            return True
        except Exception as e:
            print(f"Printing failed: {str(e)}")
            return False
