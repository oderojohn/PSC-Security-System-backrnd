from datetime import datetime
from escpos.printer import Network
import time
import re

class PackagePrinter:
    def __init__(self, ip="192.168.10.173", port=9100, max_retries=3, retry_delay=2):
        self.PRINTER_IP = ip
        self.PRINTER_PORT = port
        self.MAX_RETRIES = max_retries
        self.RETRY_DELAY = retry_delay
        self.bw_image_path = r"C:\Users\IT.Trainee\Desktop\Reception system\logo-dark.bmp"
        
        # Predefined size commands
        self.zes = [
            ('1x1', b'\x1D\x21\x00'),
            ('2x1', b'\x1D\x21\x10'),
            ('1x2', b'\x1D\x21\x01'),
            ('2x2', b'\x1D\x21\x11'),
            ('3x3', b'\x1D\x21\x22')
        ]

    def _mask_phone(self, phone):
        """Mask phone numbers to show first 4 and last 2 digits (0792******01)"""
        if not phone:
            return ""
        
        # Remove any non-digit characters
        digits = re.sub(r'\D', '', phone)
        
        if len(digits) >= 6:
            return f"{digits[:4]}******{digits[-2:]}"
        return phone  # Return original if too short to mask

    def _get_printer(self):
        """Establish connection to printer with retry logic"""
        for attempt in range(self.MAX_RETRIES):
            try:
                printer = Network(self.PRINTER_IP, self.PRINTER_PORT)
                return printer
            except Exception as e:
                if attempt == self.MAX_RETRIES - 1:
                    raise
                print(f"Connection attempt {attempt + 1} failed: {str(e)} - retrying...")
                time.sleep(self.RETRY_DELAY)
        return None

    def _set_size(self, printer, size_name):
        """Set text size using predefined zes commands"""
        for name, cmd in self.zes:
            if name == size_name:
                printer._raw(cmd)
                return
        printer._raw(self.zes[0][1])  # Default to 1x1 if not found

    def _print_common_header(self, printer, title, code):
        """Print common header for both receipt types"""
        try:
            printer.image(self.bw_image_path)
        except Exception as img_error:
            print(f"Couldn't print image: {img_error}")
        
        # Set larger size for code
        self._set_size(printer, '2x2')
        printer.set(align='center', bold=True)
        printer.text(f"{code}\n")
        self._set_size(printer, '1x1')  # Reset size
        
        printer.set(align='left', bold=False)
        printer.text("\n------------------------------------------\n")

    def print_label_receipt(self, package_data):
        """Print the package label receipt with enhanced styling"""
        printer = None
        try:
            printer = self._get_printer()
            if not printer:
                return False
                
            # Mask phone numbers before printing
            package_data['recipient_phone'] = self._mask_phone(package_data.get('recipient_phone', ''))
            package_data['dropper_phone'] = self._mask_phone(package_data.get('dropper_phone', ''))
            
            # Capitalize recipient name
            recipient_name = package_data['recipient_name'].upper()
                
            self._print_common_header(printer, "PACKAGE RECEIPT", recipient_name)
            
            # Extra large recipient name
            self._set_size(printer, '3x3')
            printer.set(align='center', bold=True)
            printer.text(recipient_name + "\n\n")
            self._set_size(printer, '1x1')  # Reset size
            
            printer.set(bold=True)
            printer.text("PACKAGE DETAILS\n")
            printer.set(bold=False)
            printer.text("-----------------------------\n")
            
            printer.text(f"Type: {package_data['type']}\n")
            printer.text(f"Code: {package_data['code']}\n")
            printer.text(f"Description: {package_data['description']}\n")
            if package_data.get('shelf'):
                printer.text(f"Shelf: {package_data['shelf']}\n")
            
            printer.text("\n")
            
            # Medium size for section headers
            self._set_size(printer, '2x1')
            printer.set(align='center', bold=True)
            printer.text("RECIPIENT INFORMATION\n")
            self._set_size(printer, '1x1')
            
            printer.set(align='left', bold=True)
            printer.text(f"Name: {recipient_name}\n")
            printer.set(bold=False)
            printer.text(f"Phone: {package_data['recipient_phone']}\n")
            
            printer.text("\n")
            printer.set(bold=True)
            printer.text("DELIVERY INFORMATION\n")
            printer.set(bold=False)
            printer.text(f"Dropped by: {package_data['dropped_by']}\n")
            printer.text(f"Phone: {package_data['dropper_phone']}\n")
            
            printer.text("\n")
            printer.text(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            if 'created_by' in package_data:
                printer.text(f"Processed by: {package_data['created_by']}\n")
            
            printer.text("\n")
            printer.set(align='center', bold=True)
            printer.text("Thank you for using\nPSC Package Service\n")
            printer.set(bold=False)
            printer.text("Handled by PSC Security\n")
            printer.text("Designed by JOHN ODERO\n\n")
            printer.cut()
            return True
        except Exception as e:
            print(f"Label print failed: {e}")
            return False
        finally:
            if printer:
                printer.close()

    def print_both_receipts(self, package_data):
        """
        Print both label and dropper receipts consecutively
        Returns tuple of (label_success, dropper_success)
        """
        label_success = self.print_label_receipt(package_data)
        return (label_success)