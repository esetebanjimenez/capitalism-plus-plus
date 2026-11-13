"""Stock market: shares, daily price, trading, dividends, M&A (gamelogic.md Stock market)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .tables import STOCK_RULES

if TYPE_CHECKING:
    from .rng import Rng

_SR = STOCK_RULES

MAX_CORPS = 12
MAX_PERSONS = 15


class Stock:
    """Per-corporation stock record."""

    __slots__ = (
        "corp_id",
        "daily_prices",
        "dilution_decay",
        "dividend_history",
        "dividend_yield_history",
        "earnings_momentum",
        "holdings_corps",
        "holdings_persons",
        "monthly_prices",
        "price",
        "total_shares",
        "trade_volume_decay",
        "yearly_earnings",
        "yearly_prices",
    )

    def __init__(self, corp_id: int, initial_value: float, price_per_share: float) -> None:
        self.corp_id = corp_id
        self.price = max(price_per_share, 0.01)
        self.total_shares = max(1, int(initial_value / self.price))
        self.holdings_corps: list[int] = [0] * MAX_CORPS
        self.holdings_persons: list[int] = [0] * MAX_PERSONS
        self.earnings_momentum = 0.0
        self.dilution_decay = 0.0
        self.trade_volume_decay = 0.0
        # History
        self.daily_prices: list[float] = []
        self.monthly_prices: list[float] = []
        self.yearly_prices: list[float] = []
        self.yearly_earnings: list[float] = []
        self.dividend_history: list[float] = []
        self.dividend_yield_history: list[float] = []

    @property
    def public_float(self) -> int:
        held = sum(self.holdings_corps) + sum(self.holdings_persons)
        return max(0, self.total_shares - held)

    @property
    def insider_held(self) -> int:
        return sum(self.holdings_corps) + sum(self.holdings_persons)

    def equity_per_share(self, equity: float) -> float:
        if self.total_shares <= 0:
            return 0.0
        return equity / self.total_shares

    def earnings_per_share(self, earnings: float) -> float:
        if self.total_shares <= 0:
            return 0.0
        return earnings / self.total_shares

    def pe_ratio(self, earnings: float) -> float:
        eps = self.earnings_per_share(earnings)
        if eps <= 0:
            return 0.0
        return self.price / eps

    def stock_return(self) -> float:
        if len(self.daily_prices) < 2:
            return 0.0
        old = self.daily_prices[0]
        if old <= 0:
            return 0.0
        return (self.price - old) / old

    def dividend_yield(self, annual_dividend: float) -> float:
        if self.price <= 0:
            return 0.0
        return annual_dividend / self.price


# ---------------------------------------------------------------------------
# Daily price movement
# ---------------------------------------------------------------------------

# Volatility bands by economic climate index (0=Excellent .. 4=Very bad)
_VOLATILITY = (0.005, 0.01, 0.02, 0.04, 0.08)


def daily_price_update(stock: Stock, rng: Rng, earnings: float, climate: int = 2) -> None:
    """Update stock price for one day (gamelogic.md Daily price movement)."""
    climate = max(0, min(4, climate))
    vol = _VOLATILITY[climate]

    # 1. Base random walk
    change = rng.uniform(-vol, vol) * stock.price

    # 2. Earnings momentum
    if earnings > 0:
        stock.earnings_momentum += _SR.momentum_up_step
    elif earnings < 0:
        stock.earnings_momentum -= _SR.momentum_down_step
    stock.earnings_momentum = max(-_SR.momentum_clamp, min(_SR.momentum_clamp, stock.earnings_momentum))
    change += stock.earnings_momentum * stock.price

    # 3. Random spikes/crashes (1/200)
    if rng.chance(_SR.spike_chance):
        spike = rng.uniform(-_SR.spike_magnitude, _SR.spike_magnitude) * stock.price
        change += spike

    # Decay factors
    stock.dilution_decay *= _SR.dilution_decay_rate
    stock.trade_volume_decay *= _SR.volume_decay_rate

    stock.price = max(0.0, stock.price + change - stock.dilution_decay - stock.trade_volume_decay)

    # Record daily price history (rolling 30)
    stock.daily_prices.append(stock.price)
    if len(stock.daily_prices) > 30:
        stock.daily_prices.pop(0)


# ---------------------------------------------------------------------------
# Trading
# ---------------------------------------------------------------------------

def price_impact(shares: int, total_shares: int, price: float) -> float:
    """Per-share price impact of a trade (gamelogic.md Price impact)."""
    if total_shares <= 0:
        return 0.0
    impact = (abs(shares) / total_shares) * price * _SR.impact_factor
    return impact


def buy_shares(
    stock: Stock, buyer_type: str, buyer_id: int, quantity: int, *, from_float: bool = True
) -> float:
    """Buy shares. Returns total cost. buyer_type is 'corp' or 'person'."""
    if quantity <= 0:
        return 0.0
    available = stock.public_float if from_float else quantity
    actual = min(quantity, available)
    if actual <= 0:
        return 0.0

    impact = price_impact(actual, stock.total_shares, stock.price)
    avg_price = stock.price + impact / 2
    total_cost = avg_price * actual

    stock.price = max(0.10, stock.price + impact)
    stock.trade_volume_decay += impact * _SR.volume_trade_factor

    if buyer_type == "corp":
        stock.holdings_corps[buyer_id] += actual
    else:
        stock.holdings_persons[buyer_id] += actual

    return total_cost


def buy_cost(stock: Stock, quantity: int, *, from_float: bool = True) -> float:
    """What buy_shares would charge, without trading (for cash checks)."""
    actual = min(quantity, stock.public_float if from_float else quantity)
    if actual <= 0:
        return 0.0
    impact = price_impact(actual, stock.total_shares, stock.price)
    return (stock.price + impact / 2) * actual


def buy_back_shares(stock: Stock, quantity: int) -> float:
    """Own-stock buyback: buy from the float and retire the shares (audit S3).

    decomp:38425-38431: cash and equity drop by the cost and total_shares falls
    by the shares bought back. Priced like any buy (S2). Returns the cost.
    """
    actual = min(quantity, stock.public_float, stock.total_shares - 1)
    if actual <= 0:
        return 0.0
    impact = price_impact(actual, stock.total_shares, stock.price)
    cost = (stock.price + impact / 2) * actual
    stock.price = max(0.10, stock.price + impact)
    stock.trade_volume_decay += impact * _SR.volume_trade_factor
    stock.total_shares -= actual
    return cost


def sell_shares(
    stock: Stock, seller_type: str, seller_id: int, quantity: int
) -> float:
    """Sell shares. Returns total proceeds."""
    if quantity <= 0:
        return 0.0

    if seller_type == "corp":
        held = stock.holdings_corps[seller_id]
    else:
        held = stock.holdings_persons[seller_id]

    actual = min(quantity, held)
    if actual <= 0:
        return 0.0

    impact = price_impact(actual, stock.total_shares, stock.price)
    avg_price = max(0.10, stock.price - impact / 2)
    total_proceeds = avg_price * actual

    stock.price = max(0.10, stock.price - impact)
    stock.trade_volume_decay -= impact * _SR.volume_trade_factor

    if seller_type == "corp":
        stock.holdings_corps[seller_id] -= actual
    else:
        stock.holdings_persons[seller_id] -= actual

    return total_proceeds


# ---------------------------------------------------------------------------
# Share issuance
# ---------------------------------------------------------------------------

def issue_shares(stock: Stock, new_shares: int) -> float:
    """Issue new shares. Returns gross proceeds (gamelogic.md Share issuance)."""
    if new_shares <= 0:
        return 0.0
    proceeds = new_shares * stock.price
    old_total = stock.total_shares
    stock.total_shares += new_shares
    # Dilute price proportionally
    dilution = stock.price * (new_shares / (old_total + new_shares))
    stock.price = max(0.10, stock.price - dilution)
    stock.dilution_decay += dilution * _SR.dilution_issue_factor
    # Reduce momentum
    stock.earnings_momentum *= _SR.issuance_momentum_factor
    return proceeds


# ---------------------------------------------------------------------------
# Dividends
# ---------------------------------------------------------------------------

def pay_dividend(stock: Stock, total_payout: float) -> dict[str, list[tuple[int, float]]]:
    """Distribute dividends proportionally to all shareholders.

    Returns {'corps': [(id, amount), ...], 'persons': [(id, amount), ...]}.
    """
    result: dict[str, list[tuple[int, float]]] = {"corps": [], "persons": []}
    if total_payout <= 0 or stock.total_shares <= 0:
        return result

    per_share = total_payout / stock.total_shares

    for i, held in enumerate(stock.holdings_corps):
        if held > 0:
            amount = held * per_share
            result["corps"].append((i, amount))

    for i, held in enumerate(stock.holdings_persons):
        if held > 0:
            amount = held * per_share
            result["persons"].append((i, amount))

    # Public float gets dividend too (goes nowhere — retained)
    stock.dividend_history.append(total_payout)
    if len(stock.dividend_history) > 30:
        stock.dividend_history.pop(0)

    dy = stock.dividend_yield(total_payout)
    stock.dividend_yield_history.append(dy)
    if len(stock.dividend_yield_history) > 30:
        stock.dividend_yield_history.pop(0)

    return result


def compute_ai_dividend(
    stock: Stock, total_assets: float, cash: float,
    investment_value: float, earnings: float,
    personality: int, rng: Rng,
) -> float:
    """Native AI dividend (FUN_00040fd5, decomp:39332). Returns total payout."""
    eps = stock.earnings_per_share(earnings)
    shares = stock.total_shares
    price = stock.price
    if shares <= 0:
        return 0.0

    # Step 1: random base from EPS
    div_ps = 0.0
    if eps > 0:
        div_ps = rng.randint(0, 59) * eps / _SR.dividend_eps_divisor

    # Step 2: cash-excess ratio vs personality threshold
    if total_assets > 0:
        ratio = (cash - total_assets) / total_assets
    else:
        ratio = 0.0
    threshold = (150 - personality) / 10.0

    # Step 3: main path — surplus cash drives payout
    if ratio > threshold:
        amount = total_assets * (ratio - threshold) / shares
        cap = price / _SR.dividend_price_cap_divisor
        if amount > cap:
            amount = cap
        main = (rng.randint(0, 89) + 10) * amount / _SR.dividend_random_divisor
        if main > div_ps:
            div_ps = main

    # Step 4: fallback — rare dividend even when cash-poor
    if div_ps == 0.0 and personality < 100:
        if rng.randint(0, 99 - personality) == 0:
            div_ps = rng.randint(0, 299) * price / _SR.dividend_fallback_divisor

    # Step 5: equity cap and minimum-payout gate
    net_equity = total_assets - investment_value
    if net_equity < _SR.dividend_equity_floor:
        net_equity = _SR.dividend_equity_floor
    if net_equity > cash:
        return 0.0
    per_share_cap = (cash - net_equity) / shares
    if per_share_cap > price:
        per_share_cap = price
    if div_ps > per_share_cap:
        div_ps = per_share_cap
    if div_ps < _SR.dividend_min_per_share:
        return 0.0

    return div_ps * shares


# ---------------------------------------------------------------------------
# Monthly / yearly processing
# ---------------------------------------------------------------------------

def stock_monthly(stock: Stock) -> None:
    """Monthly: record average price (gamelogic.md Monthly and yearly history)."""
    if stock.daily_prices:
        avg = sum(stock.daily_prices) / len(stock.daily_prices)
    else:
        avg = stock.price
    stock.monthly_prices.append(avg)
    if len(stock.monthly_prices) > 30:
        stock.monthly_prices.pop(0)


def stock_yearly(stock: Stock, annual_earnings: float) -> None:
    """Yearly: record price and earnings."""
    stock.yearly_prices.append(stock.price)
    if len(stock.yearly_prices) > 30:
        stock.yearly_prices.pop(0)
    stock.yearly_earnings.append(annual_earnings)
    if len(stock.yearly_earnings) > 30:
        stock.yearly_earnings.pop(0)


# ---------------------------------------------------------------------------
# AI trading
# ---------------------------------------------------------------------------

def ai_buyback(stock: Stock, corp_id: int, rng: Rng) -> float:
    """AI buys back own shares if public float is too high (gamelogic.md AI stock trading)."""
    if stock.total_shares <= 0:
        return 0.0
    float_ratio = stock.public_float / stock.total_shares
    if float_ratio < _SR.buyback_float_threshold:
        return 0.0
    # Buy back a fraction of the float
    target = int(stock.public_float * _SR.buyback_fraction)
    target = max(1, target)
    return buy_back_shares(stock, target)  # S3: retired, not held


def ai_invest(
    stock: Stock, investor_corp_id: int, surplus_cash: float, rng: Rng
) -> float:
    """AI invests surplus cash in another corporation's stock."""
    if surplus_cash <= 0 or stock.price <= 0:
        return 0.0
    max_shares = int(surplus_cash / stock.price)
    if max_shares <= 0:
        return 0.0
    # Don't buy more than a fraction of total shares
    limit = int(stock.total_shares * _SR.invest_max_fraction)
    quantity = min(max_shares, max(1, limit))
    cost = buy_shares(stock, "corp", investor_corp_id, quantity)
    return cost


# ---------------------------------------------------------------------------
# SEC rules
# ---------------------------------------------------------------------------

def check_sec_violation(
    buyer_corp_id: int, target_stock: Stock,
    player_person_id: int | None, player_corp_ids: list[int],
) -> bool:
    """Return True if trade would violate SEC rules (gamelogic.md Securities regulation)."""
    if player_person_id is not None:
        # Rule 1: player's corp buying stock where player personally owns shares
        if target_stock.holdings_persons[player_person_id] > 0 and buyer_corp_id in player_corp_ids:
            return True
        # Rule 3: corp buying where player personally holds shares
        if target_stock.holdings_persons[player_person_id] > 0:
            return True

    # Rule 2: controlled corp buying where main corp already owns
    for pid in player_corp_ids:
        if pid != buyer_corp_id and target_stock.holdings_corps[pid] > 0 and buyer_corp_id in player_corp_ids:
            return True

    return False


# ---------------------------------------------------------------------------
# Tender offers
# ---------------------------------------------------------------------------

def tender_offer_price(
    stock: Stock, target_is_ceo: bool, personality_trait: int, rng: Rng
) -> float:
    """Compute the price a target holder would demand (gamelogic.md Tender offers)."""
    base = stock.price
    if target_is_ceo:
        premium = 2.0 + personality_trait / 100.0
    else:
        premium = 1.3 + personality_trait / 200.0
    return base * premium * (0.9 + rng.uniform(0, 0.2))


def tender_cooldown_days(target_is_ceo: bool, success: bool, rng: Rng) -> int:
    """Cooldown after a tender offer attempt."""
    if success:
        return int(365 * 2 + rng.uniform(0, 182))
    if target_is_ceo:
        return int(365 + rng.uniform(0, 182))
    return int(182 + rng.uniform(0, 182))


# ---------------------------------------------------------------------------
# Mark-to-market (daily AI accounting)
# ---------------------------------------------------------------------------

def mark_to_market(
    stocks: list[Stock | None], corp_id: int, prev_value: float
) -> tuple[float, float]:
    """Compute current portfolio value and unrealized P&L for a corporation.

    Returns (current_value, gain_or_loss).
    """
    current = 0.0
    for stock in stocks:
        if stock is None:
            continue
        held = stock.holdings_corps[corp_id]
        if held > 0:
            current += held * stock.price
    return current, current - prev_value
