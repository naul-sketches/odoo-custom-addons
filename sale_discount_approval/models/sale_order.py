from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class SaleOrder(models.Model):
    """Extend sales order to implement tiered discount authorization workflows.

    Enforces approval requirements when order line discounts exceed
    the designated authorization threshold before quotation confirmation.
    """

    _inherit = 'sale.order'

    discount_threshold = 15.0

    approval_state = fields.Selection(
        selection=[
            ('not_required', 'Not required'),
            ('pending', 'Pending approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Approval status',
        default='not_required',
        tracking=True,
        copy=False,
        help=(
            'Workflow state indicating whether order line discounts '
            'require or received manager authorization.'
        ),
    )

    max_discount_applied = fields.Float(
        string='Max discount applied (%)',
        compute='_compute_max_discount',
        digits='Discount',
        store=True,
        help='Highest discount rate detected across commercial order lines.',
    )

    approval_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approved by',
        copy=False,
        readonly=True,
        tracking=True,
        help='Sales manager who authorized the quotation discount request.',
    )

    approval_date = fields.Datetime(
        string='Approval date',
        copy=False,
        readonly=True,
        help='Timestamp recorded when the discount request was approved.',
    )

    rejection_reason = fields.Text(
        string='Rejection reason',
        copy=False,
        tracking=True,
        help=(
            'Explanation provided by the sales manager when rejecting '
            'the discount request.'
        ),
    )

    @api.depends('order_line.discount')
    def _compute_max_discount(self):
        """Calculate the highest discount rate detected on commercial lines.

        Lines without products (such as section headings or descriptive notes)
        are excluded from this calculation.
        """
        for order in self:
            commercial_lines = order.order_line.filtered(
                lambda line: not line.display_type
            )
            discounts = commercial_lines.mapped('discount')
            order.max_discount_applied = max(discounts) if discounts else 0.0

    def action_request_approval(self):
        """Submit quotation for review when discounts exceed limit.

        Separates orders into batches based on whether discount exceeds
        authorization threshold, updating states and chatter notices.

        Returns:
            bool: True if request execution completes.
        """
        precision = self.env['decimal.precision'].precision_get('Discount')
        orders_needing_approval = self.filtered(
            lambda o: float_compare(
                o.max_discount_applied,
                self.discount_threshold,
                precision_digits=precision,
            ) > 0
        )
        orders_not_needing_approval = self - orders_needing_approval

        if orders_not_needing_approval:
            orders_not_needing_approval.write({
                'approval_state': 'not_required',
            })

        if orders_needing_approval:
            orders_needing_approval.write({
                'approval_state': 'pending',
                'rejection_reason': False,
            })
            for order in orders_needing_approval:
                order.message_post(
                    body=_(
                        "Approval requested: Order contains a maximum "
                        "discount of %.2f%%, which exceeds the allowed "
                        "limit of %.2f%%."
                    ) % (order.max_discount_applied, self.discount_threshold)
                )
        return True

    def action_approve_discount(self):
        """Authorize the quotation discount. Restricted to sales managers.

        Executes batch status updates and logs authorization notices
        in the chatter for each processed order.

        Returns:
            bool: True if approval succeeds.

        Raises:
            UserError: If current user lacks sales manager rights.
        """
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise UserError(
                _("Only sales managers can approve discounted orders.")
            )

        self.write({
            'approval_state': 'approved',
            'approval_user_id': self.env.uid,
            'approval_date': fields.Datetime.now(),
        })
        for order in self:
            msg = _("Discount authorized by %s.") % self.env.user.name
            order.message_post(body=msg)
        return True

    def action_reject_discount(self, reason=None):
        """Record the rejection reason and block the order.

        Restricted to sales managers.

        Args:
            reason (str, optional): Explanation for the rejection. If
                omitted, uses the order's existing rejection_reason field
                or a default message.

        Returns:
            bool: True if rejection succeeds.

        Raises:
            UserError: If current user lacks sales manager rights.
        """
        if not self.env.user.has_group('sales_team.group_sale_manager'):
            raise UserError(_("Only sales managers can reject orders."))

        default_rejection = _("Discount rejected by supervisor.")
        for order in self:
            rejection_text = (
                reason or order.rejection_reason or default_rejection
            )
            order.write({
                'approval_state': 'rejected',
                'rejection_reason': rejection_text,
            })
            order.message_post(
                body=_("Discount rejected: %s") % rejection_text
            )
        return True

    def _confirmation_error_message(self):
        """Prevent confirmation if discounts exceed threshold.

        Overrides Odoo confirmation hook to block orders containing line
        discounts above the threshold unless formally authorized.

        Returns:
            str or bool: Error message if blocked, or parent result.
        """
        self.ensure_one()
        precision = self.env['decimal.precision'].precision_get('Discount')
        is_discount_exceeded = (
            float_compare(
                self.max_discount_applied,
                self.discount_threshold,
                precision_digits=precision,
            ) > 0
        )
        if is_discount_exceeded and self.approval_state != 'approved':
            return _(
                "Cannot confirm order %s: The maximum discount applied "
                "(%.2f%%) exceeds the authorized threshold of %.2f%%. "
                "Manager approval is required."
            ) % (self.name, self.max_discount_applied, self.discount_threshold)
        return super()._confirmation_error_message()
