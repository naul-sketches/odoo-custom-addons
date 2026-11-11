# Sale order discount approval

[![Odoo Version](https://img.shields.io/badge/Odoo-20.0-875A7B.svg)](https://github.com/naul-sketches/odoo-custom-addons)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0.html)
[![Status](https://img.shields.io/badge/Status-Beta-yellow.svg)](https://github.com/naul-sketches/odoo-custom-addons)

Tiered approval workflow for Odoo 20 sales orders with high discounts.

---

## Overview

In standard Odoo, sales representatives can apply line discounts and confirm orders
without mandatory supervisor authorization. In wholesale and distribution businesses,
unrestricted discounts often jeopardize profit margins and complicate billing audits.

This module introduces an automated verification gate: any quotation containing order
line discounts above a designated threshold (default: 15%) is blocked from confirmation
until a sales manager reviews and formally authorizes the request.

---

## Features

* **Automated threshold detection:** Dynamically computes the maximum discount across
  all order lines using Odoo ORM stored compute methods.
* **Approval state machine:** Adds four distinct states (`Not required`,
  `Pending approval`, `Approved`, `Rejected`) integrated with Odoo tracking.
* **Confirmation enforcement:** Implements `_confirmation_error_message` hook to block
  confirmation if unapproved high discounts exist.
* **Visual warnings:** Displays alert banners on the form view when quotations require
  manager attention.
* **Audit trail:** Records approving manager identity, timestamp, and optional
  rejection notes in a dedicated notebook page and in the chatter.

---

## Configuration and permissions

* **Standard sales users:** Can create quotations and click **Request approval**
  when discounts exceed the configured authorization threshold.
* **Sales managers:** Users belonging to `sales_team.group_sale_manager` are granted
  exclusive rights to click **Approve discount** or reject orders.
* **Threshold adjustment:** The default threshold is configured via `discount_threshold`
  on the model, ready for dynamic settings integration.

---

## Usage workflow

1. Navigate to **Sales > Orders > Quotations** and create a new quotation.
2. Add order lines with discounts exceeding the authorization threshold.
3. The system flags the order as requiring approval and displays an amber alert banner.
4. Click **Request approval** to notify sales supervisors in the chatter.
5. A user with manager rights clicks **Approve discount**.
6. The quotation status switches to `Approved`, unlocking standard order confirmation.

---

## Roadmap

Planned enhancements for upcoming versions:
* Configurable discount threshold per sales team and user tier via system parameters.
* Multi-currency margin analysis to trigger approvals based on gross profit rather
  than nominal discount percentage.
* Email digest and automated activity reminders for pending approvals.

---

## Author and license

* **Author:** Luis Calero
* **Maintainer:** Luis Calero
* **License:** LGPL-3
