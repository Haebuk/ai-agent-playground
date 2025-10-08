import requests
import yfinance as yf
from typing import Type
from crewai.tools import BaseTool
from firecrawl import Firecrawl
from pydantic import BaseModel, Field
from env import FIRECRAWL_API_KEY, GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CX


def _yahoo_finance(ticker: str, period: str = "1y"):
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        info = stock.info

        if history.empty:
            return f"No data found for ticker {ticker}"

        current_price = history["Close"].iloc[-1]
        year_high = history["High"].max()
        year_low = history["Low"].min()

        revenue_growth = "N/A"
        try:
            financials = stock.financials
            if not financials.empty and "Total Revenue" in financials.index:
                revenues = financials.loc["Total Revenue"].dropna()
                if len(revenues) > 1:
                    latest_revenue = revenues.iloc[0]
                    prev_revenue = revenues.iloc[1]
                    revenue_growth = (
                        f"{(latest_revenue - prev_revenue) / prev_revenue * 100:.2f}%"
                    )
        except Exception as e:
            pass

        company_data = {
            "ticker": ticker,
            "company_name": info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "current_price": float(current_price) if current_price else None,
            "52_week_high": float(year_high),
            "52_week_low": float(year_low),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "forward_pe": info.get("forwardPE", "N/A"),
            "price_to_book": info.get("priceToBook", "N/A"),
            "revenue_growth": revenue_growth,
            "profit_margin": info.get("profitMargins", "N/A"),
            "operating_margin": info.get("operatingMargins", "N/A"),
            "debt_to_equity": info.get("debtToEquity", "N/A"),
            "return_on_equity": info.get("returnOnEquity", "N/A"),
            "dividend_yield": info.get("dividendYield", "N/A"),
            "business_summary": (
                info.get("longBusinessSummary", "N/A")[:500] + "..."
                if info.get("longBusinessSummary")
                and len(info.get("longBusinessSummary", "")) > 500
                else info.get("longBusinessSummary", "N/A")
            ),
        }

        return company_data

    except Exception as e:
        return f"Error fetching data for ticker {ticker}: {e}"


def _web_search(query: str):
    firecrawl = Firecrawl(api_key=FIRECRAWL_API_KEY)

    response = firecrawl.search(query, limit=5, integration="crewai")

    if not response:
        return f"No search results found for query: {query}"

    search_results = []

    if response.web:
        for result in response.web:
            title = getattr(result, "title", "No Title")
            url = getattr(result, "url", "")
            description = getattr(result, "description", "")

            search_results.append(
                {
                    "title": title,
                    "url": url,
                    "content": description,
                }
            )
        search_result = {
            "query": query,
            "results_count": len(search_results),
            "results": search_results,
        }
        return search_result


class WebSearchToolInput(BaseModel):
    """Input schema for WebSearchTool."""

    query: str = Field(..., description="The search query to look for.")


class WebSearchTool(BaseTool):
    name: str = "web_search_tool"
    description: str = "Searches the web for information based on a query and returns relevant results with titles, URLs, and content snippets."
    args_schema: Type[BaseModel] = WebSearchToolInput

    def _run(self, query: str):
        return _web_search(query)


class YahooFinanceToolInput(BaseModel):
    """Input schema for YahooFinanceTool."""

    ticker: str = Field(..., description="The ticker of the company to look for.")
    period: str = Field(
        default="1y", description="The p eriod of the company to look for."
    )


class YahooFinanceTool(BaseTool):
    name: str = "yahoo_finance_tool"
    description: str = """
        Retrieves a comprehensive financial and business profile for a publicly traded company using its stock ticker. It provides a wide range of data, including real-time stock price, key financial ratios (P/E, P/B, ROE), valuation metrics (market cap), growth indicators (revenue growth), and a business summary. The result is returned in a structured JSON format.
    """
    args_schema: Type[BaseModel] = YahooFinanceToolInput

    def _run(self, ticker: str, period: str = "1y"):
        return _yahoo_finance(ticker, period)


class GoogleSearchToolInput(BaseModel):
    """Input schema for GoogleSearchTool."""

    query: str = Field(..., description="The search query to look for.")
    num: int = Field(
        default=10, description="Number of search results to display (max 10)."
    )


class GoogleSearchTool(BaseTool):
    name: str = "google_search_tool"
    description: str = "Searches Google for information based on a query and returns relevant results with titles, URLs, and snippets."
    args_schema: Type[BaseModel] = GoogleSearchToolInput

    def _run(self, query: str, num: int = 10):
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_SEARCH_API_KEY,
                "cx": GOOGLE_SEARCH_CX,
                "q": query,
                "num": min(num, 10),  # API limit is 10
            }

            print(
                f"[DEBUG] Making request to Google Custom Search API with query: {query}"
            )

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            print(f"[DEBUG] Raw response type: {type(data)}")
            print(f"[DEBUG] Raw response: {data}")

            if "items" not in data or not data["items"]:
                return f"No search results found for query: {query}"

            search_results = []

            for item in data["items"]:
                title = item.get("title", "No Title")
                url = item.get("link", "")
                snippet = item.get("snippet", "")

                search_results.append(
                    {
                        "title": title,
                        "url": url,
                        "content": (
                            snippet[:500] + "..." if len(snippet) > 500 else snippet
                        ),
                    }
                )

            result = {
                "query": query,
                "results_count": len(search_results),
                "total": data.get("searchInformation", {}).get("totalResults", 0),
                "results": search_results,
            }

            print("DEBUG : ", result)

            return result

        except Exception as e:
            return f"Error searching for query '{query}': {e}"


web_search_tool = WebSearchTool()
google_search_tool = GoogleSearchTool()
yahoo_finance_tool = YahooFinanceTool()

if __name__ == "__main__":
    # test_tickers = ["NVDA", "GOOGL", "TSLA"]
    test_tickers = ["NVDA"]
    for ticker in test_tickers:
        print(f"Ticker: {ticker}")
        result = _yahoo_finance(ticker, "1d")
        print(result)
        print("--------------------------------")
