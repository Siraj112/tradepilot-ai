"use client";

import { useEffect, useState } from "react";

type CryptoMarket = {
  symbol: string;
  price_usd: number;
};

type CryptoResponse = {
  provider: string;
  data_connected: boolean;
  markets: CryptoMarket[];
};

type ForexGoldMarket = {
  symbol: string;
  price_usd: number;
  status: string;
};

type ForexGoldResponse = {
  data_connected: boolean;
  markets: ForexGoldMarket[];
};

const agents = [
  ["01", "Desk Lead", "Coordinates the AI team"],
  ["02", "Market Analyst", "Studies price and volume"],
  ["03", "Research Analyst", "Researches market events"],
  ["04", "Strategist", "Evaluates trade setups"],
  ["05", "Risk Manager", "Checks risk and exposure"],
  ["06", "Execution Trader", "Paper orders only"],
  ["07", "Trade Reviewer", "Reviews every trade"],
];

export default function Home() {
  const [crypto, setCrypto] = useState<CryptoResponse | null>(null);
  const [forexGold, setForexGold] = useState<ForexGoldResponse | null>(null);
  const [error, setError] = useState(false);
  const [updatedAt, setUpdatedAt] = useState("");

  useEffect(() => {
    let active = true;

    async function loadPrices() {
      try {
        const response = await fetch("/api/crypto", { cache: "no-store" });
        if (!response.ok) throw new Error("Crypto request failed");
        const data: CryptoResponse = await response.json();

        if (active) {
          setCrypto(data);
          setError(false);
          setUpdatedAt(new Date().toLocaleTimeString());
        }
      } catch {
        if (active) setError(true);
      }
    }

    async function loadForexGold() {
      try {
        const response = await fetch("/api/forex-gold", { cache: "no-store" });
        if (!response.ok) throw new Error("Forex/Gold request failed");
        const data: ForexGoldResponse = await response.json();
        if (active) setForexGold(data);
      } catch {
        if (active) setForexGold(null);
      }
    }

    loadPrices();
    loadForexGold();

    const timer = setInterval(() => {
      loadPrices();
      loadForexGold();
    }, 15000);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  const getPrice = (symbol: string) => {
    const market = crypto?.markets?.find(
      (item) => item.symbol === symbol
    );

    if (!market) return "Awaiting data";

    return market.price_usd.toLocaleString("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };


  const getForexGoldPrice = (symbol: string) => {
    const market = forexGold?.markets?.find((item) => item.symbol === symbol);
    if (!market || market.status !== "available") return "Awaiting data";

    return market.price_usd.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 5,
    });
  };

  const isForexGoldOnline = (symbol: string) =>
    forexGold?.markets?.some(
      (item) => item.symbol === symbol && item.status === "available"
    ) ?? false;

  const connected = crypto?.data_connected === true;

  const markets = [
    {
      name: "Bitcoin",
      symbol: "BTC / USD",
      price: getPrice("BTC"),
      icon: "₿",
      online: connected && !!crypto?.markets?.some((m) => m.symbol === "BTC"),
    },
    {
      name: "Ethereum",
      symbol: "ETH / USD",
      price: getPrice("ETH"),
      icon: "Ξ",
      online: connected && !!crypto?.markets?.some((m) => m.symbol === "ETH"),
    },
    {
      name: "Forex",
      symbol: "EUR / USD",
      price: getForexGoldPrice("EURUSD"),
      icon: "€",
      online: isForexGoldOnline("EURUSD"),
    },
    {
      name: "Forex",
      symbol: "GBP / USD",
      price: getForexGoldPrice("GBPUSD"),
      icon: "£",
      online: isForexGoldOnline("GBPUSD"),
    },
    {
      name: "Gold",
      symbol: "XAU / USD",
      price: getForexGoldPrice("XAUUSD"),
      icon: "Au",
      online: isForexGoldOnline("XAUUSD"),
    },
  ];

  return (
    <main className="min-h-screen bg-[#080d18] text-white">
      <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-5">
          <div>
            <div className="text-xl font-bold tracking-wide">
              TRADEPILOT <span className="text-cyan-400">AI</span>
            </div>
            <div className="mt-1 text-xs text-slate-400">
              Intelligent multi-market trading desk
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-2 text-xs text-amber-300">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            PAPER MODE · DEMO
          </div>
        </header>

        <section className="py-9">
          <p className="text-sm font-medium uppercase tracking-[0.25em] text-cyan-400">
            Your AI trading command center
          </p>
          <h1 className="mt-3 text-3xl font-bold leading-tight sm:text-5xl">
            Trade smarter.
            <br />
            <span className="text-cyan-400">Control every risk.</span>
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-400 sm:text-base">
            One research desk for Crypto, Forex and Gold. Analyse markets
            with a team of AI roles and test ideas with virtual money.
          </p>
        </section>

        <section className="grid gap-4 sm:grid-cols-3">
          {[
            ["VIRTUAL BALANCE", "$10,000.00", "Starting demo capital"],
            ["OPEN POSITIONS", "0", "No paper trades yet"],
            ["TRADING MODE", "Simulation", "Live trading disabled"],
          ].map(([label, value, note]) => (
            <div
              key={label}
              className="rounded-2xl border border-white/10 bg-[#111a2b] p-5"
            >
              <p className="text-xs font-medium tracking-wider text-slate-400">
                {label}
              </p>
              <p className="mt-3 text-2xl font-bold">{value}</p>
              <p className="mt-1 text-xs text-slate-500">{note}</p>
            </div>
          ))}
        </section>

        <section className="mt-9">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-xl font-bold">Markets overview</h2>
              <p className="mt-1 text-sm text-slate-400">
                Crypto prices connected to market data API
              </p>
            </div>
            <span className={`text-xs ${connected ? "text-emerald-400" : "text-amber-300"}`}>
              {connected ? "● CRYPTO DATA CONNECTED" : "● CONNECTING TO DATA"}
            </span>
          </div>

          {error && (
            <p className="mt-3 text-xs text-amber-300">
              Price refresh failed. Previous prices may be outdated.
            </p>
          )}

          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {markets.map((market) => (
              <div
                key={market.name}
                className="rounded-2xl border border-white/10 bg-[#111a2b] p-5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-2xl font-bold text-cyan-400">
                    {market.icon}
                  </span>
                  <span className={`text-[10px] font-semibold ${market.online ? "text-emerald-400" : "text-slate-500"}`}>
                    {market.online ? "● CONNECTED" : "● FEED OFFLINE"}
                  </span>
                </div>
                <h3 className="mt-5 font-semibold">{market.name}</h3>
                <p className="mt-1 text-xs text-slate-400">{market.symbol}</p>
                <p className="mt-4 text-xl font-bold">{market.price}</p>
                <p className="mt-1 text-xs text-slate-500">
                  {market.online ? "Hyperliquid mid-price · USD" : "Awaiting data connection"}
                </p>
              </div>
            ))}
          </div>

          <p className="mt-3 text-xs text-slate-500">
            {updatedAt ? `Last updated: ${updatedAt}` : "Waiting for first price update"}
            {" · "}Auto-refresh every 15 seconds
          </p>
        </section>

        <section className="mt-9">
          <h2 className="text-xl font-bold">Your AI trading team</h2>
          <p className="mt-1 text-sm text-slate-400">
            Seven specialist roles · One controlled workflow
          </p>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {agents.map(([number, name, description]) => (
              <div
                key={number}
                className="rounded-2xl border border-white/10 bg-[#111a2b] p-4"
              >
                <span className="text-xs font-bold text-cyan-400">
                  {number}
                </span>
                <h3 className="mt-3 font-semibold">{name}</h3>
                <p className="mt-1 text-xs text-slate-400">{description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mt-9 rounded-2xl border border-cyan-400/20 bg-cyan-400/5 p-5 sm:p-6">
          <h2 className="text-lg font-bold">Safety comes first</h2>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            No real orders. No connected wallets. No live broker execution.
            Every future paper trade will pass risk checks before simulation.
          </p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs text-cyan-200">
            <span className="rounded-lg bg-cyan-400/10 px-3 py-2">Risk controls planned</span>
            <span className="rounded-lg bg-cyan-400/10 px-3 py-2">Approval workflow planned</span>
            <span className="rounded-lg bg-cyan-400/10 px-3 py-2">Virtual trading planned</span>
          </div>
        </section>

        <footer className="mt-10 border-t border-white/10 py-6 text-center text-xs text-slate-500">
          TradePilot AI · Independent research and paper trading platform
        </footer>
      </div>
    </main>
  );
}
