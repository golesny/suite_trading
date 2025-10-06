from __future__ import annotations

from decimal import Decimal, getcontext, InvalidOperation

from suite_trading.domain.monetary.currency import Currency

# Set high precision for financial calculations
getcontext().prec = 28


class Money:
    """Represents a monetary amount with currency.

    Uses Python's Decimal for precision arithmetic.
    Supports values between -999,999,999,999.999999999999999999 and
    +999,999,999,999.999999999999999999
    """

    # Value limits
    MAX_VALUE = Decimal("999999999999.999999999999999999")
    MIN_VALUE = Decimal("-999999999999.999999999999999999")

    def __init__(self, value, currency: Currency):
        """Initialize Money with value and currency.

        Args:
            value: Numeric value (int, float, str, Decimal).
            currency (Currency): Currency object.

        Raises:
            ValueError: If value is invalid or out of range.
            TypeError: If currency is not Currency instance.
        """
        # Check: currency must be an instance of Currency
        if not isinstance(currency, Currency):
            raise TypeError(f"$currency must be a Currency instance, but provided value is: {currency}")

        # Check: value must be convertible to Decimal
        try:
            if isinstance(value, Decimal):
                decimal_value = value
            else:
                decimal_value = Decimal(str(value))
        except (ValueError, TypeError) as e:
            raise ValueError(f"$value cannot be converted to Decimal, but provided value is: {value}") from e

        # Check: value must be within allowed range
        if decimal_value > self.MAX_VALUE:
            raise ValueError(f"$value exceeds maximum allowed value {self.MAX_VALUE}, but provided value is: {decimal_value}")
        if decimal_value < self.MIN_VALUE:
            raise ValueError(f"$value is below minimum allowed value {self.MIN_VALUE}, but provided value is: {decimal_value}")

        # Round to currency precision
        precision_str = f"0.{'0' * currency.precision}" if currency.precision > 0 else "1"
        self._value = decimal_value.quantize(Decimal(precision_str))
        self._currency = currency

    @property
    def value(self) -> Decimal:
        """Get the decimal value."""
        return self._value

    @property
    def currency(self) -> Currency:
        """Get the currency."""
        return self._currency

    def _check_same_currency(self, other: Money) -> None:
        """Check if two Money objects have the same currency.

        Args:
            other (Money): The other Money object.

        Raises:
            ValueError: If currencies don't match.
        """
        if self.currency != other.currency:
            raise ValueError(f"Cannot operate on different currencies: {self.currency} and {other.currency}")

    # Comparison operators (same currency required)
    def __eq__(self, other) -> bool:
        """Check equality with another Money object."""
        if not isinstance(other, Money):
            return False
        if self.currency != other.currency:
            return False
        return self.value == other.value

    def __lt__(self, other) -> bool:
        """Check if this Money is less than another Money object."""
        if not isinstance(other, Money):
            return NotImplemented
        self._check_same_currency(other)
        return self.value < other.value

    def __le__(self, other) -> bool:
        """Check if this Money is less than or equal to another Money object."""
        if not isinstance(other, Money):
            return NotImplemented
        self._check_same_currency(other)
        return self.value <= other.value

    def __gt__(self, other) -> bool:
        """Check if this Money is greater than another Money object."""
        if not isinstance(other, Money):
            return NotImplemented
        self._check_same_currency(other)
        return self.value > other.value

    def __ge__(self, other) -> bool:
        """Check if this Money is greater than or equal to another Money object."""
        if not isinstance(other, Money):
            return NotImplemented
        self._check_same_currency(other)
        return self.value >= other.value

    # Arithmetic operations
    def __add__(self, other):
        """Add two Money objects (same currency) or Money + number."""
        if isinstance(other, Money):
            self._check_same_currency(other)
            return Money(self.value + other.value, self.currency)
        else:
            # Add number to Money
            try:
                return Money(self.value + Decimal(str(other)), self.currency)
            except (ValueError, TypeError):
                return NotImplemented

    def __radd__(self, other):
        """Right addition: number + Money."""
        return self.__add__(other)

    def __sub__(self, other):
        """Subtract two Money objects (same currency) or Money - number."""
        if isinstance(other, Money):
            self._check_same_currency(other)
            return Money(self.value - other.value, self.currency)
        else:
            # Subtract number from Money
            try:
                return Money(self.value - Decimal(str(other)), self.currency)
            except (ValueError, TypeError):
                return NotImplemented

    def __rsub__(self, other):
        """Right subtraction: number - Money."""
        try:
            return Money(Decimal(str(other)) - self.value, self.currency)
        except (ValueError, TypeError):
            return NotImplemented

    def __mul__(self, other):
        """Multiply Money by number (returns Money)."""
        if isinstance(other, Money):
            return NotImplemented  # Money * Money doesn't make sense
        try:
            return Money(self.value * Decimal(str(other)), self.currency)
        except (ValueError, TypeError):
            return NotImplemented

    def __rmul__(self, other):
        """Right multiplication: number * Money."""
        return self.__mul__(other)

    def __truediv__(self, other):
        """Divide Money by number (returns Money) or Money by Money (returns Decimal)."""
        if isinstance(other, Money):
            self._check_same_currency(other)
            if other.value == 0:
                raise ZeroDivisionError("Cannot divide by zero Money")
            return self.value / other.value  # Returns Decimal ratio
        else:
            try:
                divisor = Decimal(str(other))
                if divisor == 0:
                    raise ZeroDivisionError("Cannot divide Money by zero")
                return Money(self.value / divisor, self.currency)
            except (ValueError, TypeError):
                return NotImplemented

    def __rtruediv__(self, other):
        """Right division: number / Money (not supported)."""
        return NotImplemented

    def __neg__(self):
        """Return negative Money."""
        return Money(-self.value, self.currency)

    def __pos__(self):
        """Return positive Money (copy)."""
        return Money(self.value, self.currency)

    def __abs__(self):
        """Return absolute Money."""
        return Money(abs(self.value), self.currency)

    # String representations
    def __str__(self) -> str:
        """Return string like '1000.50 USD'."""
        return f"{self.value} {self.currency.code}"

    def __repr__(self) -> str:
        """Return string like 'Money(1000.50, USD)'."""
        return f"{self.__class__.__name__}({self.value}, {self.currency.code})"

    def __hash__(self) -> int:
        """Hash based on value and currency code."""
        return hash((self.value, self.currency.code))

    @classmethod
    def from_str(cls, value_str: str) -> Money:
        """Parse Money from string like '1000.50 USD'.

        Args:
            value_str (str): String representation.

        Returns:
            Money: Money object.

        Raises:
            ValueError: If string format is invalid.
        """
        value_str = value_str.strip()
        if not value_str:
            raise ValueError("Value string with $value_str = '' cannot be empty")

        # Split by whitespace
        parts = value_str.split()
        if len(parts) != 2:
            raise ValueError(f"Value string with $value_str = '{value_str}' must be in format 'value currency_code'")

        value_part, currency_part = parts

        try:
            value = Decimal(value_part)
        except (ValueError, TypeError, InvalidOperation) as e:
            raise ValueError(f"Invalid value part '{value_part}' in string '{value_str}'") from e

        try:
            currency = Currency.from_str(currency_part)
        except ValueError as e:
            raise ValueError(f"Invalid currency part '{currency_part}' in string '{value_str}'") from e

        return cls(value, currency)
