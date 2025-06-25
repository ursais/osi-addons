from odoo.addons.stock_delivery.models.delivery_request_objects import DeliveryPackage


class OnLogicDeliveryPackage(DeliveryPackage):
    """ """

    def apply_uplift(self, company):
        """
        Apply the uplift to the weight and volume of the package
        """
        if company.use_delivery_uplift:
            self.dimension = {
                "length": self.dimension["length"] * (1 + company.delivery_dimension_uplift / 100),
                "width": self.dimension["width"] * (1 + company.delivery_dimension_uplift / 100),
                "height": self.dimension["height"] * (1 + company.delivery_dimension_uplift / 100),
            }
