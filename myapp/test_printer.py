from printer_service import PackagePrinter  # Assuming your class is in package_printer.py
from datetime import datetime

def test_package_printer():
    # Initialize the printer
    printer = PackagePrinter()  # Use default IP/port or specify your own
    
    # Create sample package data
    package_data = {
        'type': "Parcel",
        'code': "PKG-2023-12345",
        'description': "Amazon delivery - Electronics",
        'shelf': "A12",
        'recipient_name': "JOHN DOE",
        'recipient_phone': "+254712345678",
        'dropped_by': "Amazon Courier",
        'dropper_phone': "+254798765432",
        'created_by': "PSC Reception",
    }

    print("Testing package label receipt...")
    label_success = printer.print_label_receipt(package_data)
    print(f"Label receipt print {'succeeded' if label_success else 'failed'}")

    # Wait a moment between prints
    input("Press Enter to print the dropper receipt...")

    print("\nTesting dropper receipt...")
    dropper_success = printer.print_dropper_receipt(package_data)
    print(f"Dropper receipt print {'succeeded' if dropper_success else 'failed'}")

if __name__ == "__main__":
    test_package_printer()