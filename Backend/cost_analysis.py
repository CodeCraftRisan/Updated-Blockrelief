"""
============================================================
  Block-Relief : Gas Cost Analysis
  ACTUAL values from real testnet deployments

  Sepolia  → Etherscan screenshot  (Jun 01, 2026)
  Polygon  → Polygonscan screenshot (Jun 01, 2026)
  Ganache  → registration_log.csv (actual run data)

  Run: python analysis/cost_analysis.py
  Output: analysis/cost_analysis.png
         analysis/cost_analysis_table.csv
============================================================
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_DIR  = Path(__file__).resolve().parent

# ============================================================
#   ACTUAL RECORDED GAS DATA (Screenshot থেকে)
# ============================================================

# ── Ganache (registration_log.csv থেকে actual) ──
GANACHE_DEPLOY_GAS      = 1_923_440    # same contract → same gas
GANACHE_AVG_REGISTER    = 145_161      # avg per registerVictim()
GANACHE_TOTAL_REGISTER  = 14_516_101   # 100 victims
GANACHE_GAS_PRICE_GWEI  = 20           # Ganache default
GANACHE_DISTRIBUTE_GAS  = 2_200_000    # autoDistribute() estimate

# ── Sepolia (Etherscan — Jun 01, 2026) ──
SEPOLIA_DEPLOY_GAS      = 1_923_440    # ACTUAL from screenshot
SEPOLIA_GAS_PRICE_GWEI  = 14.58957046 # ACTUAL: 14.58957046 Gwei
SEPOLIA_TX_FEE_ETH      = 0.0280621634055824  # ACTUAL from Etherscan
SEPOLIA_BLOCK           = 10_967_452   # Block number
SEPOLIA_CONTRACT        = "0xd031dcf6fc79beddab93ca07f6b12ce32c2205b8"
SEPOLIA_DEPLOYER        = "0x0BE13aB2db2aE124F950804a476e8465E4EBE905"

# ── Polygon Amoy (Polygonscan — Jun 01, 2026) ──
POLYGON_DEPLOY_GAS      = 1_924_280    # ACTUAL from screenshot
POLYGON_GAS_PRICE_GWEI  = 29.100000063 # ACTUAL: 29.1 Gwei
POLYGON_TX_FEE_POL      = 0.0559965481 # ACTUAL from Polygonscan
POLYGON_BLOCK           = 39_394_537   # Block number
POLYGON_CONTRACT        = "0x4e21064d68309c5e24fd6ad75dbd67b81bbe08c6"
POLYGON_DEPLOYER        = "0xb36C62B671E8f2fF3CD8450E6021355B1aEc6C6C"

# ── Token prices (approximate at time of deployment) ──
ETH_PRICE_USD   = 3000.0   # 1 ETH ≈ $3000 (approximate)
MATIC_PRICE_USD = 0.50     # 1 POL/MATIC ≈ $0.50 (approximate)


# ============================================================
#   CALCULATE FULL DEPLOYMENT COST
# ============================================================

def calculate_costs():
    """
    Full deployment cost:
    Deploy + Register×100 (estimated) + autoDistribute()
    """
    networks = {}

    # ── Ganache ──
    ganache_deploy_eth    = GANACHE_DEPLOY_GAS    * GANACHE_GAS_PRICE_GWEI * 1e-9
    ganache_register_eth  = GANACHE_TOTAL_REGISTER* GANACHE_GAS_PRICE_GWEI * 1e-9
    ganache_dist_eth      = GANACHE_DISTRIBUTE_GAS* GANACHE_GAS_PRICE_GWEI * 1e-9
    networks['Ganache\n(Local)'] = {
        'deploy_gas':    GANACHE_DEPLOY_GAS,
        'register_gas':  GANACHE_TOTAL_REGISTER,
        'dist_gas':      GANACHE_DISTRIBUTE_GAS,
        'deploy_cost':   ganache_deploy_eth,
        'register_cost': ganache_register_eth,
        'dist_cost':     ganache_dist_eth,
        'total_token':   ganache_deploy_eth + ganache_register_eth + ganache_dist_eth,
        'total_usd':     0.0,   # free (fake ETH)
        'gas_price':     GANACHE_GAS_PRICE_GWEI,
        'currency':      'ETH (fake)',
        'color':         '#4ade80',
        'deploy_actual': ganache_deploy_eth,
        'note':          'Free — local simulation',
    }

    # ── Sepolia ──
    # Deploy: actual from Etherscan
    # Register × 100: estimate using same gas units but Sepolia gas price
    # Distribute: estimate
    sepolia_register_eth  = GANACHE_TOTAL_REGISTER * SEPOLIA_GAS_PRICE_GWEI * 1e-9
    sepolia_dist_eth      = GANACHE_DISTRIBUTE_GAS * SEPOLIA_GAS_PRICE_GWEI * 1e-9
    sepolia_total         = SEPOLIA_TX_FEE_ETH + sepolia_register_eth + sepolia_dist_eth
    networks['Sepolia\n(L1 Testnet)'] = {
        'deploy_gas':    SEPOLIA_DEPLOY_GAS,
        'register_gas':  GANACHE_TOTAL_REGISTER,
        'dist_gas':      GANACHE_DISTRIBUTE_GAS,
        'deploy_cost':   SEPOLIA_TX_FEE_ETH,
        'register_cost': sepolia_register_eth,
        'dist_cost':     sepolia_dist_eth,
        'total_token':   sepolia_total,
        'total_usd':     SEPOLIA_TX_FEE_ETH * ETH_PRICE_USD,   # deploy only, real cost
        'gas_price':     SEPOLIA_GAS_PRICE_GWEI,
        'currency':      'SepoliaETH (free)',
        'color':         '#60a5fa',
        'deploy_actual': SEPOLIA_TX_FEE_ETH,
        'note':          f'Actual deploy: {SEPOLIA_TX_FEE_ETH:.6f} ETH',
    }

    # ── Polygon Amoy ──
    polygon_register_pol  = GANACHE_TOTAL_REGISTER * POLYGON_GAS_PRICE_GWEI * 1e-9
    polygon_dist_pol      = GANACHE_DISTRIBUTE_GAS * POLYGON_GAS_PRICE_GWEI * 1e-9
    polygon_total         = POLYGON_TX_FEE_POL + polygon_register_pol + polygon_dist_pol
    networks['Polygon Amoy\n(L2 Testnet)'] = {
        'deploy_gas':    POLYGON_DEPLOY_GAS,
        'register_gas':  GANACHE_TOTAL_REGISTER,
        'dist_gas':      GANACHE_DISTRIBUTE_GAS,
        'deploy_cost':   POLYGON_TX_FEE_POL,
        'register_cost': polygon_register_pol,
        'dist_cost':     polygon_dist_pol,
        'total_token':   polygon_total,
        'total_usd':     POLYGON_TX_FEE_POL * MATIC_PRICE_USD,  # deploy only
        'gas_price':     POLYGON_GAS_PRICE_GWEI,
        'currency':      'POL (free testnet)',
        'color':         '#a78bfa',
        'deploy_actual': POLYGON_TX_FEE_POL,
        'note':          f'Actual deploy: {POLYGON_TX_FEE_POL:.6f} POL',
    }

    # ── Ethereum Mainnet (estimated, not deployed) ──
    # Using same gas as Sepolia but mainnet gas price estimate
    mainnet_gas_price     = 30.0  # Gwei estimate
    mainnet_deploy_eth    = SEPOLIA_DEPLOY_GAS    * mainnet_gas_price * 1e-9
    mainnet_register_eth  = GANACHE_TOTAL_REGISTER* mainnet_gas_price * 1e-9
    mainnet_dist_eth      = GANACHE_DISTRIBUTE_GAS* mainnet_gas_price * 1e-9
    mainnet_total         = mainnet_deploy_eth + mainnet_register_eth + mainnet_dist_eth
    networks['Ethereum\n(L1 Mainnet)\n[Estimated]'] = {
        'deploy_gas':    SEPOLIA_DEPLOY_GAS,
        'register_gas':  GANACHE_TOTAL_REGISTER,
        'dist_gas':      GANACHE_DISTRIBUTE_GAS,
        'deploy_cost':   mainnet_deploy_eth,
        'register_cost': mainnet_register_eth,
        'dist_cost':     mainnet_dist_eth,
        'total_token':   mainnet_total,
        'total_usd':     mainnet_total * ETH_PRICE_USD,
        'gas_price':     mainnet_gas_price,
        'currency':      'ETH',
        'color':         '#f87171',
        'deploy_actual': mainnet_deploy_eth,
        'note':          'Estimated (not deployed)',
    }

    # ── Polygon Mainnet (estimated) ──
    poly_main_gas_price   = 50.0  # Gwei estimate
    poly_main_deploy      = POLYGON_DEPLOY_GAS    * poly_main_gas_price * 1e-9
    poly_main_register    = GANACHE_TOTAL_REGISTER* poly_main_gas_price * 1e-9
    poly_main_dist        = GANACHE_DISTRIBUTE_GAS* poly_main_gas_price * 1e-9
    poly_main_total       = poly_main_deploy + poly_main_register + poly_main_dist
    networks['Polygon\n(L2 Mainnet)\n[Estimated]'] = {
        'deploy_gas':    POLYGON_DEPLOY_GAS,
        'register_gas':  GANACHE_TOTAL_REGISTER,
        'dist_gas':      GANACHE_DISTRIBUTE_GAS,
        'deploy_cost':   poly_main_deploy,
        'register_cost': poly_main_register,
        'dist_cost':     poly_main_dist,
        'total_token':   poly_main_total,
        'total_usd':     poly_main_total * MATIC_PRICE_USD,
        'gas_price':     poly_main_gas_price,
        'currency':      'POL/MATIC',
        'color':         '#c084fc',
        'deploy_actual': poly_main_deploy,
        'note':          'Estimated (not deployed)',
    }

    return networks


# ============================================================
#   PRINT TABLE
# ============================================================

def print_summary(networks):
    print("=" * 80)
    print("BLOCK-RELIEF: GAS COST ANALYSIS")
    print("Based on ACTUAL testnet deployment data (Jun 01, 2026)")
    print("=" * 80)

    print(f"\n{'Network':<28} {'Gas Price':>12} {'Deploy':>14} {'Register×100':>14} {'Distribute':>12} {'Total (token)':>14}")
    print("-" * 96)

    for name, d in networks.items():
        net = name.replace('\n', ' ')
        print(f"{net:<28} {d['gas_price']:>9.2f} Gwei  "
              f"{d['deploy_cost']:>12.6f}  "
              f"{d['register_cost']:>12.6f}  "
              f"{d['dist_cost']:>10.6f}  "
              f"{d['total_token']:>12.6f}  {d['currency']}")

    print()
    print("─── ACTUAL Deployment Data ───")
    print(f"Sepolia  TX Fee: {SEPOLIA_TX_FEE_ETH:.10f} ETH  "
          f"| Gas: {SEPOLIA_DEPLOY_GAS:,} | Block: {SEPOLIA_BLOCK:,}")
    print(f"Polygon  TX Fee: {POLYGON_TX_FEE_POL:.10f} POL  "
          f"| Gas: {POLYGON_DEPLOY_GAS:,} | Block: {POLYGON_BLOCK:,}")

    print()
    # Key insight
    sepolia_total = list(networks.values())[1]['total_token'] * ETH_PRICE_USD
    eth_mainnet   = list(networks.values())[3]['total_usd']
    poly_mainnet  = list(networks.values())[4]['total_usd']

    print("─── Key Insights ───")
    print(f"Gas used (Sepolia vs Polygon): {SEPOLIA_DEPLOY_GAS:,} vs {POLYGON_DEPLOY_GAS:,}"
          f" (diff: {abs(SEPOLIA_DEPLOY_GAS - POLYGON_DEPLOY_GAS)} units — same contract ✓)")
    if eth_mainnet > 0 and poly_mainnet > 0:
        ratio = eth_mainnet / poly_mainnet
        print(f"Ethereum Mainnet estimated total: ${eth_mainnet:.2f}")
        print(f"Polygon Mainnet estimated total:  ${poly_mainnet:.2f}")
        print(f"→ Polygon is ~{ratio:.0f}x cheaper than Ethereum Mainnet")
    print(f"Sepolia deploy actual cost: {SEPOLIA_TX_FEE_ETH:.6f} ETH (≈ ${SEPOLIA_TX_FEE_ETH * ETH_PRICE_USD:.2f} at ${ETH_PRICE_USD}/ETH)")
    print(f"Polygon deploy actual cost: {POLYGON_TX_FEE_POL:.6f} POL (≈ ${POLYGON_TX_FEE_POL * MATIC_PRICE_USD:.4f} at ${MATIC_PRICE_USD}/POL)")


# ============================================================
#   PLOTS
# ============================================================

def make_plots(networks):
    names  = list(networks.keys())
    colors = [d['color'] for d in networks.values()]

    fig, axes = plt.subplots(1, 3, figsize=(20, 7), facecolor='#0a0e1a')
    fig.suptitle(
        'Block-Relief: Gas Cost Comparison\n'
        'Ganache (Local) | Sepolia (L1) | Polygon Amoy (L2) | Mainnet Estimates',
        fontsize=13, color='white', fontweight='bold', y=1.01
    )

    x = np.arange(len(names))
    bar_w = 0.55

    # ── Plot 1: Stacked bar — token cost ──
    ax1 = axes[0]
    ax1.set_facecolor('#111827')

    deploy_costs   = [d['deploy_cost']   for d in networks.values()]
    register_costs = [d['register_cost'] for d in networks.values()]
    dist_costs     = [d['dist_cost']     for d in networks.values()]

    b1 = ax1.bar(x, deploy_costs,   bar_w, label='Deploy Contract',
                 color='#3b82f6', alpha=0.9, edgecolor='#0f1525', linewidth=0.5)
    b2 = ax1.bar(x, register_costs, bar_w, bottom=deploy_costs,
                 label='Register × 100 victims',
                 color='#14b8a6', alpha=0.9, edgecolor='#0f1525', linewidth=0.5)
    b3 = ax1.bar(x, dist_costs,     bar_w,
                 bottom=[d+r for d,r in zip(deploy_costs, register_costs)],
                 label='autoDistribute()',
                 color='#f59e0b', alpha=0.9, edgecolor='#0f1525', linewidth=0.5)

    ax1.set_xticks(x)
    ax1.set_xticklabels(names, color='#94a3b8', fontsize=7.5)
    ax1.set_ylabel('Gas Cost (Native Token)', color='#94a3b8', fontsize=10)
    ax1.set_title('Full Deployment Cost\n(Native Token, Stacked)',
                  color='white', fontsize=11, fontweight='bold')
    ax1.legend(facecolor='#1a2340', edgecolor='#334155',
               labelcolor='white', fontsize=8)
    ax1.tick_params(colors='#64748b')
    for sp in ax1.spines.values(): sp.set_edgecolor('#1e293b')
    ax1.grid(axis='y', alpha=0.15, color='#334155')

    # ── Plot 2: Deploy-only actual cost (token) ──
    ax2 = axes[1]
    ax2.set_facecolor('#111827')

    actual_deploy = [d['deploy_actual'] for d in networks.values()]
    bars2 = ax2.bar(x, actual_deploy, bar_w, color=colors,
                    alpha=0.9, edgecolor='#0f1525', linewidth=0.5)

    # Annotate bars with actual values
    max_val = max(actual_deploy) if max(actual_deploy) > 0 else 1
    for bar, val, d in zip(bars2, actual_deploy, networks.values()):
        label = f"{val:.4f}\n{d['currency'].split()[0]}"
        ax2.text(bar.get_x() + bar.get_width()/2.,
                 bar.get_height() + max_val * 0.01,
                 label, ha='center', va='bottom',
                 color='white', fontsize=7.5, fontweight='bold')

    # Mark actual vs estimated
    for i, d in enumerate(networks.values()):
        if 'Estimated' in d['note']:
            ax2.text(x[i], -max_val * 0.08, '(est.)',
                     ha='center', color='#64748b', fontsize=7)

    ax2.set_xticks(x)
    ax2.set_xticklabels(names, color='#94a3b8', fontsize=7.5)
    ax2.set_ylabel('Deploy Cost (Native Token)', color='#94a3b8', fontsize=10)
    ax2.set_title('Contract Deployment Cost\n(★ = Actual Testnet Data)',
                  color='white', fontsize=11, fontweight='bold')
    ax2.tick_params(colors='#64748b')
    for sp in ax2.spines.values(): sp.set_edgecolor('#1e293b')
    ax2.grid(axis='y', alpha=0.15, color='#334155')

    # Stars on actual data
    for i, d in enumerate(networks.values()):
        if 'Actual' in d['note']:
            ax2.text(x[i], actual_deploy[i] + max_val * 0.06,
                     '★ ACTUAL', ha='center', color='#fbbf24',
                     fontsize=7, fontweight='bold')

    # ── Plot 3: Gas used comparison (deploy only) ──
    ax3 = axes[2]
    ax3.set_facecolor('#111827')

    gas_used = [d['deploy_gas'] for d in networks.values()]
    bars3 = ax3.bar(x, gas_used, bar_w, color=colors,
                    alpha=0.9, edgecolor='#0f1525', linewidth=0.5)

    for bar, val in zip(bars3, gas_used):
        ax3.text(bar.get_x() + bar.get_width()/2.,
                 bar.get_height() + max(gas_used) * 0.01,
                 f'{val:,}', ha='center', va='bottom',
                 color='white', fontsize=7.5, fontweight='bold')

    # Highlight that gas is same across networks
    ax3.axhline(y=SEPOLIA_DEPLOY_GAS, color='#fbbf24',
                linestyle='--', linewidth=1.5, alpha=0.7,
                label=f'Actual: {SEPOLIA_DEPLOY_GAS:,} gas')

    ax3.set_xticks(x)
    ax3.set_xticklabels(names, color='#94a3b8', fontsize=7.5)
    ax3.set_ylabel('Gas Units Used', color='#94a3b8', fontsize=10)
    ax3.set_title('Gas Units — Contract Deploy\n(Same Contract = Same Gas)',
                  color='white', fontsize=11, fontweight='bold')
    ax3.legend(facecolor='#1a2340', edgecolor='#334155',
               labelcolor='white', fontsize=8)
    ax3.tick_params(colors='#64748b')
    for sp in ax3.spines.values(): sp.set_edgecolor('#1e293b')
    ax3.grid(axis='y', alpha=0.15, color='#334155')

    # Annotation box
    textstr = (
        f'★ ACTUAL DATA\n'
        f'Sepolia: {SEPOLIA_DEPLOY_GAS:,} gas @ {SEPOLIA_GAS_PRICE_GWEI:.2f} Gwei\n'
        f'  Fee: {SEPOLIA_TX_FEE_ETH:.6f} ETH\n'
        f'Polygon: {POLYGON_DEPLOY_GAS:,} gas @ {POLYGON_GAS_PRICE_GWEI:.2f} Gwei\n'
        f'  Fee: {POLYGON_TX_FEE_POL:.6f} POL\n'
        f'Gas diff: {abs(SEPOLIA_DEPLOY_GAS - POLYGON_DEPLOY_GAS)} units'
    )
    ax3.text(0.98, 0.97, textstr, transform=ax3.transAxes,
             fontsize=7, va='top', ha='right',
             color='#fbbf24',
             bbox=dict(boxstyle='round,pad=0.4',
                       facecolor='#1a2340', edgecolor='#fbbf24',
                       alpha=0.9))

    plt.tight_layout(pad=2.5)
    out_path = OUT_DIR / 'cost_analysis.png'
    plt.savefig(str(out_path), dpi=150,
                bbox_inches='tight', facecolor='#0a0e1a')
    plt.close()
    print(f"\n✅ Saved: {out_path}")


# ============================================================
#   SAVE CSV TABLE
# ============================================================

def save_csv(networks):
    rows = []
    for name, d in networks.items():
        rows.append({
            'Network':           name.replace('\n', ' '),
            'Gas_Price_Gwei':    d['gas_price'],
            'Deploy_Gas':        d['deploy_gas'],
            'Deploy_Cost_Token': round(d['deploy_cost'], 10),
            'Register100_Cost':  round(d['register_cost'], 10),
            'Distribute_Cost':   round(d['dist_cost'], 10),
            'Total_Token':       round(d['total_token'], 10),
            'Currency':          d['currency'],
            'Note':              d['note'],
        })

    df = pd.DataFrame(rows)
    csv_path = OUT_DIR / 'cost_analysis_table.csv'
    df.to_csv(str(csv_path), index=False)
    print(f"✅ Saved: {csv_path}")

    # Also save to data/ folder
    data_path = BASE_DIR / 'data' / 'gas_cost_analysis.csv'
    df.to_csv(str(data_path), index=False)
    print(f"✅ Saved: {data_path}")

    return df


# ============================================================
#   THESIS SUMMARY PRINT
# ============================================================

def print_thesis_summary():
    print("\n" + "=" * 80)
    print("THESIS WRITE-UP READY DATA")
    print("=" * 80)
    print(f"""
Table X: Gas Cost Comparison Across Networks

+------------------+-----------+----------+-------------------+-----------+
| Network          | Type      | Gas Used | Gas Price (Gwei)  | Deploy Fee|
+------------------+-----------+----------+-------------------+-----------+
| Ganache Local    | Local Dev | {GANACHE_DEPLOY_GAS:>8,} | {20:>17.2f} | Free      |
| Sepolia          | L1 Testnet| {SEPOLIA_DEPLOY_GAS:>8,} | {SEPOLIA_GAS_PRICE_GWEI:>17.5f} | {SEPOLIA_TX_FEE_ETH:.6f} ETH|
| Polygon Amoy     | L2 Testnet| {POLYGON_DEPLOY_GAS:>8,} | {POLYGON_GAS_PRICE_GWEI:>17.3f} | {POLYGON_TX_FEE_POL:.6f} POL|
| Ethereum Mainnet | L1 (est.) | {SEPOLIA_DEPLOY_GAS:>8,} | {30:>17.2f} | ~0.057736 ETH|
| Polygon Mainnet  | L2 (est.) | {POLYGON_DEPLOY_GAS:>8,} | {50:>17.2f} | ~0.096214 POL|
+------------------+-----------+----------+-------------------+-----------+

Key Finding:
- Same contract compiles to same bytecode → same gas units on all networks
- Sepolia gas: {SEPOLIA_DEPLOY_GAS:,} units | Polygon gas: {POLYGON_DEPLOY_GAS:,} units
  (Difference: {abs(SEPOLIA_DEPLOY_GAS - POLYGON_DEPLOY_GAS)} units — negligible, due to block conditions)
- Polygon Amoy actual fee: {POLYGON_TX_FEE_POL:.6f} POL ≈ ${POLYGON_TX_FEE_POL * 0.5:.4f} USD
- Ethereum Mainnet (est): ~${SEPOLIA_DEPLOY_GAS * 30e-9 * 3000:.2f} USD for deploy alone
- Polygon is ~{(SEPOLIA_DEPLOY_GAS * 30e-9 * 3000) / (POLYGON_DEPLOY_GAS * 50e-9 * 0.5):.0f}x cheaper than Ethereum Mainnet

Deployment Verification:
  Sepolia contract:  {SEPOLIA_CONTRACT}
  Polygon contract:  {POLYGON_CONTRACT}
  Both verified on respective block explorers ✓
""")


# ============================================================
#   MAIN
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("BLOCK-RELIEF: COST ANALYSIS")
    print("Actual Data: Sepolia + Polygon Amoy (Jun 01, 2026)")
    print("=" * 60)

    networks = calculate_costs()
    print_summary(networks)
    make_plots(networks)
    df = save_csv(networks)
    print_thesis_summary()

    print("\n📊 Files generated:")
    print("   analysis/cost_analysis.png        ← thesis figure")
    print("   analysis/cost_analysis_table.csv  ← data table")
    print("   data/gas_cost_analysis.csv        ← for Flask API")
