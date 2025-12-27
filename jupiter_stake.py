#!/usr/bin/env python3
"""CLI Tool: Automatischer Jupiter Swap SOL → Staking Token"""

import asyncio
import sys
sys.path.insert(0, '/workspaces/omni-profit-solana-bot')

from src.trading.auto_stake_swap import AutoStakeSwap

async def main():
    print("=" * 70)
    print("🌊 Jupiter Auto-Stake: SOL → Staking Token")  
    print("=" * 70)
    print()
    
    # Show options
    print("Wähle Ziel-Token:")
    print("  1. jitoSOL  (Jito)       - 7.5% APY - Höchste Rewards")
    print("  2. mSOL     (Marinade)   - 7.0% APY - Beste Liquidität")
    print("  3. bSOL     (BlazeStake) - 6.8% APY")
    print("  4. rSOL     (Raydium)    - 6.5% APY")
    print()
    
    choice = input("Deine Wahl (1-4) [1]: ").strip() or "1"
    
    token_map = {
        "1": "jitoSOL",
        "2": "mSOL",
        "3": "bSOL",
        "4": "rSOL",
    }
    
    target_token = token_map.get(choice, "jitoSOL")
    print(f"✅ Gewählt: {target_token}")
    print()
    
    # Get percentage
    percentage = input("Prozent zu staken (z.B. 90) [90]: ").strip() or "90"
    try:
        percentage = float(percentage)
        if not (0 < percentage <= 100):
            raise ValueError()
    except:
        print("❌ Ungültige Eingabe, verwende 90%")
        percentage = 90.0
    
    print()
    print(f"⚙️  Konfiguration:")
    print(f"   Token: {target_token}")
    print(f"   Amount: {percentage}% deiner SOL")
    print(f"   Reserve: {100-percentage}% für Gas")
    print()
    
    # Confirm
    mode = input("Modus - (S)imulation oder (R)eal? [S]: ").strip().upper() or "S"
    simulate_only = mode != "R"
    
    if not simulate_only:
        print()
        print("⚠️  WARNUNG: Realer Swap wird ausgeführt!")
        confirm = input("Fortfahren? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("❌ Abgebrochen")
            return
    
    print()
    print("🔄 Starte Swap...")
    print()
    
    try:
        async with AutoStakeSwap() as swapper:
            # Show balance
            balance = await swapper.get_sol_balance()
            print(f"💰 Aktuelle Balance: {balance:.6f} SOL")
            print()
            
            # Execute
            result = await swapper.auto_stake(
                target_token=target_token,
                percentage=percentage,
                min_reserve_sol=0.02,
                simulate_only=simulate_only,
            )
            
            print()
            if result.success:
                print("✅ Swap erfolgreich!")
                print(f"   Input:  {result.input_amount:.6f} SOL")
                print(f"   Output: {result.output_amount:.6f} {target_token}")
                print(f"   Rate:   {result.output_amount/result.input_amount:.4f}")
                
                if simulate_only:
                    print()
                    print("ℹ️  Dies war eine Simulation")
                    print("   Setze ALLOW_REAL_TRANSACTIONS=true für echten Swap")
                else:
                    print()
                    print("🎉 Transaktion abgeschlossen!")
                    print(f"   Signature: {result.signature}")
            else:
                print(f"❌ Swap fehlgeschlagen: {result.error}")
                
                if "Jupiter API" in str(result.error):
                    print()
                    print("💡 Jupiter API nicht erreichbar in Codespace")
                    print("   Verwende Web Interface:")
                    print(f"   https://jup.ag/swap/SOL-{target_token}")
    
    except KeyboardInterrupt:
        print("\n❌ Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
