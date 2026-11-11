from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestSaleDiscountApproval(TransactionCase):
    """Test suite for sale order discount approval workflow."""

    @classmethod
    def setUpClass(cls):
        """Set up test customers, products, and users with role groups."""
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Commercial Test Customer',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Commercial Test Product',
            'list_price': 100.0,
        })
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Sales Manager Test User',
            'login': 'sales_manager_test',
            'groups_id': [
                (6, 0, [cls.env.ref('sales_team.group_sale_manager').id])
            ],
        })
        cls.standard_user = cls.env['res.users'].create({
            'name': 'Standard Sales User',
            'login': 'sales_standard_test',
            'groups_id': [
                (6, 0, [cls.env.ref('sales_team.group_sale_order_user').id])
            ],
        })

    def test_01_confirm_standard_order_passes(self):
        """Verify standard 10% discount confirms without approval."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
                'discount': 10.0,
            })],
        })
        order.action_confirm()
        self.assertEqual(
            order.state,
            'sale',
            "Standard order must confirm without approval.",
        )

    def test_02_confirm_high_discount_raises_user_error(self):
        """Verify order with 25% discount is blocked from confirmation."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'discount': 25.0,
            })],
        })
        with self.assertRaises(UserError):
            order.action_confirm()

    def test_03_manager_approval_allows_confirmation(self):
        """Verify manager approval unlocks order confirmation."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'discount': 20.0,
            })],
        })
        order.action_request_approval()
        self.assertEqual(
            order.approval_state,
            'pending',
            "State must be pending approval.",
        )

        # Manager authorizes the order
        order.with_user(self.manager_user).action_approve_discount()
        self.assertEqual(
            order.approval_state,
            'approved',
            "State must be approved.",
        )

        # Confirmation now succeeds
        order.action_confirm()
        self.assertEqual(
            order.state,
            'sale',
            "Order must confirm once approved.",
        )

    def test_04_manager_rejection_blocks_order(self):
        """Verify sales manager can reject high discounts with notes."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'discount': 30.0,
            })],
        })
        order.action_request_approval()
        order.with_user(self.manager_user).action_reject_discount(
            reason="Discount exceeds commercial policy."
        )
        self.assertEqual(
            order.approval_state,
            'rejected',
            "State must be rejected.",
        )
        self.assertEqual(
            order.rejection_reason,
            "Discount exceeds commercial policy.",
        )

        with self.assertRaises(UserError):
            order.action_confirm()

    def test_05_unauthorized_user_cannot_approve(self):
        """Verify standard sales users cannot approve discounts."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'discount': 20.0,
            })],
        })
        order.action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.standard_user).action_approve_discount()

    def test_06_exact_threshold_discount_confirms_without_approval(self):
        """Verify discount exactly at 15% confirms without approval."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'discount': 15.0,
            })],
        })
        order.action_confirm()
        self.assertEqual(
            order.state,
            'sale',
            "Orders with discount at threshold must confirm directly.",
        )
