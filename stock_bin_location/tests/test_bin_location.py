"""
@tagged('post_install')
class TestBinLocation(TransactionCase):
    def SetupClass(cls):
        super(TestBinLocation, cls).SetupClass()

    def ReceiveStorableProduct(self):
        # Set Dye Lot and Serial and Bin Location
        self.assertEqual(True, False)

    def ManageInventory(self):
        # Change the Bin Location on Lot/Serial grid view
        self.assertEqual(True, False)

    def ViewReporting(self):
        # Open Inventory Report and see Bin Location field
        self.assertEqual(True, False)

    def DeliverProduct(self):
        # Via Delivery Operation. Choose from available inventory and can see the Bin Location on each line
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
"""
