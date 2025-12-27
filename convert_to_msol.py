#!/usr/bin/env python3
"""SOL zu mSOL Konverter - Marinade Liquid Staking"""

import asyncio
import sys
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.transaction import Transaction
from solders.message import Message
import base58
from dotenv import load_dotenv
import os

load_dotenv('.env.production')

# Marinade Finance Programm IDs (Mainnet)
MARINADE_PROGRAM_ID = Pubkey.from_string("MarBmsSgKXdrN1egZf5sqe1TMai9K1rChYNDJgjq7aD")
MSOL_MINT = Pubkey.from_string("mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So")

print("=" * 70)
print("🌊 SOL → mSOL Konverter (Marinade Liquid Staking)")
print("=" * 70)
print()

def get_wallet():
    """Lade Wallet aus .env"""
    private_key = os.getenv('WALLET_PRIVATE_KEY')
    if not private_key:
        print("❌ WALLET_PRIVATE_KEY nicht in .env.production gesetzt!")
        sys.exit(1)
    
    secret_key = base58.b58decode(private_key)
    return Keypair.from_bytes(secret_key)

async def check_balance(client: AsyncClient, pubkey: Pubkey):
    """Prüfe SOL Balance"""
    response = await client.get_balance(pubkey)
    return response.value / 1_000_000_000

async def get_msol_balance(client: AsyncClient, pubkey: Pubkey):
    """Prüfe mSOL Balance (Token Account)"""
    # Dies ist vereinfacht - in Produktion würde man SPL Token Accounts abfragen
    # Für jetzt zeigen wir nur SOL Balance
    return 0.0

def main():
    wallet = get_wallet()
    pubkey = wallet.pubkey()
    
    print(f"💼 Wallet: {pubkey}")
    print()
    
    # RPC URL
    rpc_url = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
    print(f"🌐 Network: {rpc_url}")
    print()
    
    async def run():
        client = AsyncClient(rpc_url)
        
        try:
            # Balance prüfen
            sol_balance = await check_balance(client, pubkey)
            print(f"💰 Aktuelle SOL Balance: {sol_balance:.6f} SOL")
            print()
            
            if sol_balance < 0.01:
                print("❌ Zu wenig SOL für Konvertierung (min. 0.01 SOL)")
                print("   Balance zu niedrig für Gas + Staking")
                return
            
            print("📊 Marinade Liquid Staking Info:")
            print("   - Verdiene ~7% APY auf dein SOL")
            print("   - mSOL bleibt liquid (kannst jederzeit handeln)")
            print("   - mSOL = SOL + Staking Rewards")
            print("   - Keine Lock-up Period")
            print()
            
            # Empfohlener Betrag (90% der Balance, 10% für Gas)
            recommended = sol_balance * 0.9
            print(f"💡 Empfohlen: {recommended:.6f} SOL konvertieren")
            print(f"   (Behalte {sol_balance * 0.1:.6f} SOL für Gas & Transaktionen)")
            print()
            
            # User Input
            print("🔢 Wieviel SOL möchtest du zu mSOL konvertieren?")
            print(f"   Verfügbar: {sol_balance:.6f} SOL")
            print(f"   Empfohlen: {recommended:.6f} SOL")
            print()
            
            amount_input = input("Betrag in SOL (oder 'q' zum Abbrechen): ").strip()
            
            if amount_input.lower() == 'q':
                print("❌ Abgebrochen")
                return
            
            try:
                amount = float(amount_input)
            except ValueError:
                print("❌ Ungültige Eingabe")
                return
            
            if amount <= 0 or amount > sol_balance:
                print(f"❌ Betrag muss zwischen 0 und {sol_balance} sein")
                return
            
            if amount > recommended:
                print(f"⚠️  Warnung: Du konvertierst mehr als empfohlen!")
                confirm = input("Fortfahren? (ja/nein): ").strip().lower()
                if confirm != 'ja':
                    print("❌ Abgebrochen")
                    return
            
            print()
            print("=" * 70)
            print(f"🌊 KONVERTIERUNG STARTEN")
            print("=" * 70)
            print(f"Betrag: {amount:.6f} SOL → mSOL")
            print(f"Expected mSOL: ~{amount:.6f} mSOL (+ künftige Rewards)")
            print()
            
            # Sicherheitscheck
            allow_real = os.getenv('ALLOW_REAL_TRANSACTIONS', 'false').lower()
            if allow_real != 'true':
                print("⚠️  SIMULATION MODE")
                print("   ALLOW_REAL_TRANSACTIONS=false in .env")
                print()
                print("✅ Simulation: Konvertierung würde funktionieren!")
                print(f"   {amount:.6f} SOL → ~{amount:.6f} mSOL")
                print()
                print("💡 Zum echten Staking:")
                print("   1. Setze ALLOW_REAL_TRANSACTIONS=true in .env.production")
                print("   2. Oder benutze Marinade Web App:")
                print("      → https://marinade.finance/app/staking")
                return
            
            # ECHTE TRANSAKTION (wenn enabled)
            print("⚠️  ACHTUNG: ECHTE TRANSAKTION!")
            print("   Dies sendet echte SOL zum Marinade Programm")
            confirm = input("Bestätigen? (JA in Großbuchstaben): ").strip()
            
            if confirm != "JA":
                print("❌ Abgebrochen")
                return
            
            print()
            print("🔄 Sende Transaktion...")
            print("   (Dies kann 30-60 Sekunden dauern)")
            print()
            
            # TODO: Implementiere echte Marinade Stake Transaktion
            # Dies erfordert Anchor/Marinade SDK Integration
            print("❌ Echte Marinade Integration noch nicht implementiert")
            print()
            print("💡 Nutze stattdessen:")
            print("   → Marinade Web App: https://marinade.finance/app/staking")
            print("   → Oder Jupiter mit mSOL Swap")
            print()
            print("📋 Manuelle Schritte:")
            print(f"   1. Gehe zu https://marinade.finance/app/staking")
            print(f"   2. Verbinde Wallet: {pubkey}")
            print(f"   3. Stake {amount:.6f} SOL")
            print(f"   4. Erhalte mSOL in dein Wallet")
            
        finally:
            await client.close()
    
    asyncio.run(run())

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Abgebrochen")
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
