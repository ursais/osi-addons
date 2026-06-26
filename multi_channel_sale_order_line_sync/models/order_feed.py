# Copyright (C) 2026 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Append newly-added channel line items onto already-confirmed Sales Orders.

Background
----------
The Webkul "Odoo Multi-Channel Sale" connector (``order.feed``) imports orders
from external channels (Shopify, etc.).  When a third-party app such as
"One Click Upsell" edits a Shopify order *after* it was first created, the
channel re-sends the order with one or more extra line items.  The connector
re-evaluates the feed, but because the matching Odoo Sales Order has already
left the ``draft`` state it only synchronises the order *state* and logs
"Only order state can be update as order not in draft state" -- silently
dropping the new line item.  The fulfilment team then has to add the missing
line by hand.

This module bridges that gap without touching the third-party connector: after
the standard feed import runs (and also on demand / via cron), it compares the
line items captured in the feed against the linked confirmed Sales Order and
appends any genuinely-new lines.

Design notes
------------
* The connector's internal field/method names vary between versions, so every
  access to connector-owned fields is done defensively (``_fields`` lookups,
  candidate name lists, ``sudo``) and the whole reconciliation is wrapped so it
  can never break the standard import flow.
* Matching is done on a ``(product, quantity)`` multiset so that legitimate
  duplicate lines are preserved and only the truly missing additions are added.
* The behaviour is gated by a global setting (default: enabled) so admins can
  switch it off if needed.
"""
import logging
from collections import Counter
from datetime import datetime, timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

PARAM_ENABLED = "multi_channel_sale_order_line_sync.append_to_confirmed"

# Candidate field names on ``order.feed`` that reference the channel/instance.
_FEED_CHANNEL_FIELDS = ("channel_id", "instance_id")
# Candidate field names holding the feed's line items.
_FEED_LINE_FIELDS = ("line_ids", "order_line_ids", "feed_line_ids", "order_line")
# Candidate field names on a feed line for quantity / price / sku / name.
_LINE_QTY_FIELDS = ("product_uom_qty", "quantity", "qty", "order_qty", "line_qty")
_LINE_PRICE_FIELDS = ("price_unit", "price", "item_price", "unit_price", "line_price")
_LINE_CODE_FIELDS = ("default_code", "sku", "code", "product_default_code")
_LINE_NAME_FIELDS = ("name", "product_name", "description", "title")
# Candidate field names on a feed line referencing the product (m2o or store id).
_LINE_PRODUCT_FIELDS = (
    "product_id",
    "product_variant_id",
    "store_product_id",
    "variant_id",
    "product_template_id",
)
# Candidate fields on ``order.feed`` directly linking the ERP sale order.
_FEED_ORDER_FIELDS = (
    "order_id",
    "sale_order_id",
    "erp_order_id",
    "erp_id",
    "order_name",
)
# Candidate mapping models / fields used by the connector to link orders.
_ORDER_MAPPING_MODELS = ("channel.order.mappings", "sale.channel.mapping")
_MAP_STORE_ID_FIELDS = ("store_order_id", "store_id", "store_reference")
_MAP_ORDER_FIELDS = (
    "order_name",
    "erp_id",
    "order_id",
    "sale_order_id",
    "erp_order_id",
)
# Candidate fields on ``sale.order`` that may store the channel order reference.
_SO_STORE_REF_FIELDS = ("store_order_id", "channel_order_ref", "store_id")


class OrderFeed(models.Model):
    _inherit = "order.feed"

    # ------------------------------------------------------------------
    # Hook into the standard import flow
    # ------------------------------------------------------------------
    def import_items(self, *args, **kwargs):
        """Run the connector import, then reconcile missing confirmed-order lines.

        ``*args/**kwargs`` keep this override signature-tolerant across connector
        versions.  The reconciliation is best-effort and never raises, so a
        failure here can never interrupt the standard import.
        """
        res = super().import_items(*args, **kwargs)
        try:
            self.sudo()._mc_sync_missing_lines()
        except Exception:  # pragma: no cover - defensive guard
            _logger.exception(
                "Multi-channel confirmed-order line sync failed for feeds %s",
                self.ids,
            )
        return res

    # ------------------------------------------------------------------
    # Public entry points (server action / cron)
    # ------------------------------------------------------------------
    def action_mc_sync_missing_lines(self):
        """Manually reconcile selected feeds (bound to the Action menu)."""
        self.sudo()._mc_sync_missing_lines()
        return True

    @api.model
    def _cron_mc_sync_missing_lines(self, days=2):
        """Reconcile feeds touched in the last ``days`` days (opt-in cron)."""
        since = fields.Datetime.to_string(datetime.now() - timedelta(days=days))
        feeds = self.sudo().search([("write_date", ">=", since)])
        if feeds:
            feeds._mc_sync_missing_lines()
        return True

    # ------------------------------------------------------------------
    # Core reconciliation
    # ------------------------------------------------------------------
    def _mc_sync_missing_lines(self):
        """Append feed line items missing from each linked confirmed order."""
        if not self._mc_sync_enabled():
            return
        for feed in self:
            try:
                feed._mc_sync_missing_lines_one()
            except Exception:  # pragma: no cover - isolate per-feed failures
                _logger.exception(
                    "Failed to sync missing lines for order.feed %s", feed.id
                )

    def _mc_sync_missing_lines_one(self):
        self.ensure_one()
        order = self._mc_get_sale_order()
        if not order:
            return
        # Draft/sent quotations are already handled natively by the connector;
        # we only need to cover orders that have left the editable state.
        if order.state != "sale":
            return
        if "locked" in order._fields and order.locked:
            _logger.info(
                "order.feed %s: linked order %s is locked; skipping auto line "
                "append (manual review required).",
                self.id,
                order.name,
            )
            return

        feed_lines = self._mc_get_feed_lines()
        if not feed_lines:
            return

        # Build a multiset of (product_id, rounded_qty) already on the order so
        # that genuine duplicates are preserved and only new lines are added.
        existing = Counter()
        for line in order.order_line:
            if line.display_type or not line.product_id:
                continue
            existing[(line.product_id.id, self._mc_round(line.product_uom_qty))] += 1

        new_line_vals = []
        for fline in feed_lines:
            product = self._mc_resolve_product(fline)
            if not product:
                _logger.info(
                    "order.feed %s: could not resolve a product for a feed line; "
                    "skipping it.",
                    self.id,
                )
                continue
            qty = self._mc_line_float(fline, _LINE_QTY_FIELDS, default=1.0) or 1.0
            key = (product.id, self._mc_round(qty))
            if existing.get(key, 0) > 0:
                existing[key] -= 1
                continue
            price = self._mc_line_float(fline, _LINE_PRICE_FIELDS, default=None)
            name = self._mc_line_str(fline, _LINE_NAME_FIELDS)
            new_line_vals.append((product, qty, price, name))

        if not new_line_vals:
            return

        added = self._mc_append_lines(order, new_line_vals)
        if added:
            order.message_post(
                body=_(
                    "Multi-Channel Sale Order Line Sync added %(count)s line(s) "
                    "from channel feed %(feed)s that were missing from this "
                    "confirmed order:%(lines)s"
                )
                % {
                    "count": len(added),
                    "feed": self.display_name,
                    "lines": "".join(
                        "<br/>- %s (x%s)" % (p.display_name, self._mc_round(q))
                        for p, q, _price, _name in new_line_vals
                    ),
                }
            )

    # ------------------------------------------------------------------
    # Helpers: append lines
    # ------------------------------------------------------------------
    def _mc_append_lines(self, order, new_line_vals):
        """Create the missing order lines; return the created records."""
        SaleOrderLine = self.env["sale.order.line"].sudo()
        created = SaleOrderLine.browse()
        for product, qty, price, name in new_line_vals:
            vals = {
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": qty,
            }
            try:
                line = SaleOrderLine.create(vals)
                # Preserve the channel-supplied (possibly discounted) unit price.
                if price is not None:
                    line.price_unit = price
                if name:
                    line.name = name
                created |= line
            except Exception:  # pragma: no cover - keep going on per-line errors
                _logger.exception(
                    "order.feed %s: failed to append product %s to order %s",
                    self.id,
                    product.display_name,
                    order.name,
                )
        return created

    # ------------------------------------------------------------------
    # Helpers: locate the linked sale order
    # ------------------------------------------------------------------
    def _mc_get_sale_order(self):
        self.ensure_one()
        SaleOrder = self.env["sale.order"].sudo()

        # 1. Direct relation on the feed.
        for fname in _FEED_ORDER_FIELDS:
            field = self._fields.get(fname)
            if field and field.type == "many2one" and field.comodel_name == "sale.order":
                value = self[fname]
                if value:
                    return value

        # 2. Connector order-mapping model.
        order = self._mc_order_from_mapping()
        if order:
            return order

        # 3. Fallback: match by channel order reference stored on the SO.
        store_ref = self._mc_store_order_ref()
        if store_ref:
            for fname in _SO_STORE_REF_FIELDS:
                if fname in SaleOrder._fields:
                    order = SaleOrder.search([(fname, "=", str(store_ref))], limit=1)
                    if order:
                        return order

        # 4. Last resort: customer reference == feed name (e.g. "#41516").
        feed_ref = self.display_name if "name" not in self._fields else self.name
        if feed_ref and "client_order_ref" in SaleOrder._fields:
            order = SaleOrder.search([("client_order_ref", "=", feed_ref)], limit=1)
            if order:
                return order
        return SaleOrder.browse()

    def _mc_order_from_mapping(self):
        store_ref = self._mc_store_order_ref()
        channel = self._mc_channel()
        for model_name in _ORDER_MAPPING_MODELS:
            if model_name not in self.env:
                continue
            Mapping = self.env[model_name].sudo()
            domain = []
            sid_field = self._mc_first_field(Mapping, _MAP_STORE_ID_FIELDS)
            if sid_field and store_ref:
                domain.append((sid_field, "=", str(store_ref)))
            if channel and "channel_id" in Mapping._fields:
                domain.append(("channel_id", "=", channel.id))
            if not domain:
                continue
            mapping = Mapping.search(domain, limit=1)
            if not mapping:
                continue
            for fname in _MAP_ORDER_FIELDS:
                field = mapping._fields.get(fname)
                if (
                    field
                    and field.type == "many2one"
                    and field.comodel_name == "sale.order"
                    and mapping[fname]
                ):
                    return mapping[fname]
        return self.env["sale.order"].browse()

    # ------------------------------------------------------------------
    # Helpers: feed introspection
    # ------------------------------------------------------------------
    def _mc_channel(self):
        for fname in _FEED_CHANNEL_FIELDS:
            field = self._fields.get(fname)
            if field and field.type == "many2one" and self[fname]:
                return self[fname]
        return False

    def _mc_store_order_ref(self):
        for fname in ("store_id", "store_order_id", "store_reference"):
            if fname in self._fields and self[fname]:
                return self[fname]
        return False

    def _mc_get_feed_lines(self):
        for fname in _FEED_LINE_FIELDS:
            field = self._fields.get(fname)
            if field and field.type in ("one2many", "many2many"):
                return self[fname]
        return self.env["order.feed"].browse()  # empty fallback

    def _mc_resolve_product(self, fline):
        """Resolve a feed line to a ``product.product`` defensively."""
        Product = self.env["product.product"].sudo()

        # 1. By internal reference / SKU.
        code = self._mc_line_str(fline, _LINE_CODE_FIELDS)
        if code:
            product = Product.search([("default_code", "=", code)], limit=1)
            if product:
                return product

        # 2. By direct many2one product field on the feed line.
        for fname in _LINE_PRODUCT_FIELDS:
            field = fline._fields.get(fname)
            if not field or field.type != "many2one":
                continue
            value = fline[fname]
            if not value:
                continue
            if field.comodel_name == "product.product":
                return value
            if field.comodel_name == "product.template":
                return value.product_variant_id

        # 3. By store product id via connector product-mapping models.
        store_pid = self._mc_line_str(fline, ("product_id", "store_product_id", "variant_id"))
        if store_pid:
            product = self._mc_product_from_mapping(store_pid)
            if product:
                return product
        return False

    def _mc_product_from_mapping(self, store_pid):
        for model_name in ("channel.product.mappings", "channel.template.mappings"):
            if model_name not in self.env:
                continue
            Mapping = self.env[model_name].sudo()
            sid_field = self._mc_first_field(
                Mapping, ("store_product_id", "store_id", "product_store_id")
            )
            if not sid_field:
                continue
            mapping = Mapping.search([(sid_field, "=", str(store_pid))], limit=1)
            if not mapping:
                continue
            for fname in ("product_name", "odoo_product_id", "product_id", "erp_id"):
                field = mapping._fields.get(fname)
                if not field or field.type != "many2one" or not mapping[fname]:
                    continue
                if field.comodel_name == "product.product":
                    return mapping[fname]
                if field.comodel_name == "product.template":
                    return mapping[fname].product_variant_id
        return False

    # ------------------------------------------------------------------
    # Generic primitives
    # ------------------------------------------------------------------
    @staticmethod
    def _mc_round(value):
        return float(round(value or 0.0, 4))

    @staticmethod
    def _mc_first_field(record, names):
        for name in names:
            if name in record._fields:
                return name
        return None

    @staticmethod
    def _mc_line_float(record, names, default=0.0):
        for name in names:
            if name in record._fields:
                value = record[name]
                if value not in (False, None, ""):
                    try:
                        return float(value)
                    except (TypeError, ValueError):
                        continue
        return default

    @staticmethod
    def _mc_line_str(record, names):
        for name in names:
            if name in record._fields:
                value = record[name]
                # A many2one would not be a useful string here; skip non-scalars.
                if value and isinstance(value, str):
                    return value.strip()
        return False

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    @api.model
    def _mc_sync_enabled(self):
        value = self.env["ir.config_parameter"].sudo().get_param(PARAM_ENABLED, "1")
        return str(value).lower() not in ("0", "false", "")
