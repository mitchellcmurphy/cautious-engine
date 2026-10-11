class TickerNotFoundError(Exception):
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        super().__init__(f"Ticker not found: {ticker}")


class NoRecentFilingsError(Exception):
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        super().__init__(f"No recent filings found for: {ticker}")


class UpstreamServiceError(Exception):
    def __init__(self, service: str, detail: str) -> None:
        self.service = service
        self.detail = detail
        super().__init__(f"{service} request failed: {detail}")


class SummarizationError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"Summarization failed: {detail}")
