#!/usr/bin/env python3
"""
Forward Testing Simulation - Paper Trading with Scoring System
Simulates trades based on scoring system recommendations.

Usage:
    python3 forward_test_simulation.py --score-threshold 65 --days 1
    python3 forward_test_simulation.py --continuous  # Run continuously
"""

import argparse
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

from premarket_analysis.config import TICKERS
from premarket_analysis.main_with_scoring import analyze_ticker_with_scoring
from premarket_analysis.market_data import get_et_time_naive

class PaperTrade:
    """Represents a simulated trade."""
    
    def __init__(self, ticker: str, entry_price: float, score: float, 
                 analysis_data: Dict, position_size: float = 100.0):
        self.ticker = ticker
        self.entry_price = entry_price
        self.entry_time = datetime.now()
        self.score = score
        self.analysis_data = analysis_data
        self.position_size = position_size
        self.status = 'OPEN'
        self.exit_price = None
        self.exit_time = None
        self.exit_reason = None
        self.pnl = 0.0
        
        # Calculate stops based on ATR
        atr_pct = analysis_data.get('atr_pct', 3.0)
        self.stop_loss = entry_price * (1 - (atr_pct / 100) * 1.5)  # 1.5x ATR
        self.take_profit = entry_price * (1 + (atr_pct / 100) * 2.5)  # 2.5x ATR (1.67 R:R)
    
    def check_exit(self, current_price: float, current_time: datetime) -> bool:
        """Check if trade should be exited."""
        if self.status != 'OPEN':
            return False
        
        # Check stop loss
        if current_price <= self.stop_loss:
            self.exit_price = self.stop_loss
            self.exit_time = current_time
            self.exit_reason = 'STOP_LOSS'
            self.status = 'CLOSED'
            self.pnl = (self.exit_price - self.entry_price) / self.entry_price * self.position_size
            return True
        
        # Check take profit
        if current_price >= self.take_profit:
            self.exit_price = self.take_profit
            self.exit_time = current_time
            self.exit_reason = 'TAKE_PROFIT'
            self.status = 'CLOSED'
            self.pnl = (self.exit_price - self.entry_price) / self.entry_price * self.position_size
            return True
        
        # Time-based exit (close after 3 days)
        if (current_time - self.entry_time).days >= 3:
            self.exit_price = current_price
            self.exit_time = current_time
            self.exit_reason = 'TIME_EXIT_3D'
            self.status = 'CLOSED'
            self.pnl = (self.exit_price - self.entry_price) / self.entry_price * self.position_size
            return True
        
        return False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging."""
        return {
            'ticker': self.ticker,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat(),
            'score': self.score,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'status': self.status,
            'exit_price': self.exit_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'exit_reason': self.exit_reason,
            'pnl': self.pnl,
            'rsi': self.analysis_data.get('rsi'),
            'bb_status': self.analysis_data.get('bb_status'),
            'trend': self.analysis_data.get('trend'),
            'sentiment': self.analysis_data.get('sentiment')
        }


class ForwardTestSimulator:
    """Manages forward testing simulation."""
    
    def __init__(self, score_threshold: float = 65, max_positions: int = 3, 
                 position_size: float = 100.0):
        self.score_threshold = score_threshold
        self.max_positions = max_positions
        self.position_size = position_size
        self.open_trades: List[PaperTrade] = []
        self.closed_trades: List[PaperTrade] = []
        self.log_file = f'forward_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
    def scan_for_signals(self) -> List[Dict]:
        """Scan all tickers and return qualifying signals."""
        print(f"\n{'='*80}")
        print(f"🔍 SCANNING FOR SIGNALS - {get_et_time_naive().strftime('%Y-%m-%d %H:%M ET')}")
        print(f"{'='*80}")
        
        signals = []
        
        for ticker in TICKERS:
            try:
                result = analyze_ticker_with_scoring(ticker)
                
                # Check if qualifies
                score = result.get('score', 0)
                if score >= self.score_threshold:
                    # Additional quality checks
                    quality_flags = result.get('score_quality_flags', [])
                    if not quality_flags or not any('WARNING' in flag for flag in quality_flags):
                        signals.append(result)
                        print(f"   ✅ {ticker}: Score {score:.0f} - QUALIFIED")
                    else:
                        print(f"   ⚠️  {ticker}: Score {score:.0f} - Quality issues: {quality_flags}")
                else:
                    print(f"   ⏭️  {ticker}: Score {score:.0f} - Below threshold")
                    
            except Exception as e:
                print(f"   ❌ {ticker}: Error - {e}")
        
        return signals
    
    def enter_trade(self, signal: Dict) -> PaperTrade:
        """Enter a new paper trade."""
        ticker = signal['ticker']
        price = signal['price']
        score = signal['score']
        
        trade = PaperTrade(
            ticker=ticker,
            entry_price=price,
            score=score,
            analysis_data=signal,
            position_size=self.position_size
        )
        
        self.open_trades.append(trade)
        
        print(f"\n🟢 ENTERED TRADE:")
        print(f"   Ticker: {ticker}")
        print(f"   Entry: ${price:.2f}")
        print(f"   Score: {score:.0f}/100")
        print(f"   Stop Loss: ${trade.stop_loss:.2f} ({((trade.stop_loss/price - 1)*100):.1f}%)")
        print(f"   Take Profit: ${trade.take_profit:.2f} ({((trade.take_profit/price - 1)*100):.1f}%)")
        print(f"   Position Size: ${self.position_size:.2f}")
        
        return trade
    
    def update_positions(self):
        """Update all open positions and check for exits."""
        if not self.open_trades:
            return
        
        print(f"\n{'='*80}")
        print(f"📊 UPDATING {len(self.open_trades)} OPEN POSITIONS")
        print(f"{'='*80}")
        
        for trade in self.open_trades[:]:  # Copy list to allow modification
            try:
                # Get current analysis
                result = analyze_ticker_with_scoring(trade.ticker)
                current_price = result['price']
                
                # Calculate unrealized P&L
                unrealized_pnl = (current_price - trade.entry_price) / trade.entry_price * self.position_size
                
                print(f"\n   {trade.ticker}:")
                print(f"   Entry: ${trade.entry_price:.2f} → Current: ${current_price:.2f}")
                print(f"   Unrealized P&L: ${unrealized_pnl:+.2f} ({(unrealized_pnl/self.position_size*100):+.1f}%)")
                print(f"   Stop: ${trade.stop_loss:.2f} | Target: ${trade.take_profit:.2f}")
                
                # Check for exit
                if trade.check_exit(current_price, datetime.now()):
                    print(f"   🔔 EXITED: {trade.exit_reason}")
                    print(f"   Exit Price: ${trade.exit_price:.2f}")
                    print(f"   P&L: ${trade.pnl:+.2f} ({(trade.pnl/self.position_size*100):+.1f}%)")
                    
                    self.open_trades.remove(trade)
                    self.closed_trades.append(trade)
                    
            except Exception as e:
                print(f"   ❌ Error updating {trade.ticker}: {e}")
    
    def print_summary(self):
        """Print performance summary."""
        if not self.closed_trades:
            print("\n📊 No closed trades yet")
            return
        
        wins = [t for t in self.closed_trades if t.pnl > 0]
        losses = [t for t in self.closed_trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in self.closed_trades)
        win_rate = len(wins) / len(self.closed_trades) * 100 if self.closed_trades else 0
        avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0
        avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0
        
        print(f"\n{'='*80}")
        print(f"📊 SIMULATION SUMMARY")
        print(f"{'='*80}")
        print(f"Closed Trades: {len(self.closed_trades)}")
        print(f"Win Rate: {win_rate:.1f}% ({len(wins)}W / {len(losses)}L)")
        print(f"Total P&L: ${total_pnl:+.2f}")
        print(f"Average Win: ${avg_win:+.2f}")
        print(f"Average Loss: ${avg_loss:+.2f}")
        
        if avg_loss != 0:
            profit_factor = abs(avg_win * len(wins) / (avg_loss * len(losses)))
            print(f"Profit Factor: {profit_factor:.2f}")
        
        print(f"\nOpen Positions: {len(self.open_trades)}")
        
        # Show recent trades
        print(f"\n🔄 Recent Trades:")
        for trade in self.closed_trades[-5:]:
            pnl_pct = (trade.pnl / self.position_size * 100)
            emoji = "🟢" if trade.pnl > 0 else "🔴"
            print(f"   {emoji} {trade.ticker}: ${trade.pnl:+.2f} ({pnl_pct:+.1f}%) - {trade.exit_reason} (Score: {trade.score:.0f})")
    
    def save_log(self):
        """Save trades to JSON log file."""
        log_data = {
            'simulation_start': datetime.now().isoformat(),
            'parameters': {
                'score_threshold': self.score_threshold,
                'max_positions': self.max_positions,
                'position_size': self.position_size
            },
            'open_trades': [t.to_dict() for t in self.open_trades],
            'closed_trades': [t.to_dict() for t in self.closed_trades]
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        # Also save as CSV for easy analysis
        if self.closed_trades:
            df = pd.DataFrame([t.to_dict() for t in self.closed_trades])
            csv_file = self.log_file.replace('.json', '.csv')
            df.to_csv(csv_file, index=False)
            print(f"\n💾 Results saved to: {self.log_file} and {csv_file}")
    
    def run_single_scan(self):
        """Run one scan and update positions."""
        # Update existing positions
        self.update_positions()
        
        # Scan for new signals
        signals = self.scan_for_signals()
        
        # Enter new trades if we have room
        available_slots = self.max_positions - len(self.open_trades)
        
        if signals and available_slots > 0:
            print(f"\n{'='*80}")
            print(f"🎯 FOUND {len(signals)} QUALIFYING SIGNALS")
            print(f"   Available position slots: {available_slots}")
            print(f"{'='*80}")
            
            # Sort by score and take top ones
            signals.sort(key=lambda x: x['score'], reverse=True)
            
            for signal in signals[:available_slots]:
                self.enter_trade(signal)
        elif not signals:
            print(f"\n⏸️  No qualifying signals at this time")
        else:
            print(f"\n⏸️  Max positions reached ({len(self.open_trades)}/{self.max_positions})")
        
        # Print summary
        self.print_summary()
        
        # Save log
        self.save_log()


def main():
    parser = argparse.ArgumentParser(description='Forward test the scoring system')
    parser.add_argument('--score-threshold', type=float, default=65,
                       help='Minimum score to enter trade (default: 65)')
    parser.add_argument('--max-positions', type=int, default=3,
                       help='Maximum concurrent positions (default: 3)')
    parser.add_argument('--position-size', type=float, default=100.0,
                       help='Position size in dollars (default: 100)')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously (scan every 30 minutes)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Scan interval in minutes for continuous mode (default: 30)')
    
    args = parser.parse_args()
    
    print("="*80)
    print("🚀 FORWARD TESTING SIMULATION")
    print("="*80)
    print(f"Score Threshold: {args.score_threshold}+")
    print(f"Max Positions: {args.max_positions}")
    print(f"Position Size: ${args.position_size:.2f}")
    
    if args.continuous:
        print(f"Mode: Continuous (every {args.interval} minutes)")
    else:
        print(f"Mode: Single scan")
    
    simulator = ForwardTestSimulator(
        score_threshold=args.score_threshold,
        max_positions=args.max_positions,
        position_size=args.position_size
    )
    
    if args.continuous:
        print(f"\n🔄 Starting continuous scanning...")
        print(f"   Press Ctrl+C to stop\n")
        
        try:
            while True:
                simulator.run_single_scan()
                
                next_scan = datetime.now() + timedelta(minutes=args.interval)
                print(f"\n⏰ Next scan at {next_scan.strftime('%H:%M:%S')}")
                print(f"   Sleeping for {args.interval} minutes...\n")
                
                time.sleep(args.interval * 60)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping simulation...")
            simulator.print_summary()
            simulator.save_log()
            print("\n✅ Simulation stopped\n")
    else:
        # Single scan
        simulator.run_single_scan()
        print("\n✅ Single scan complete\n")


if __name__ == "__main__":
    main()
